from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from scipy.stats import pearsonr as scipy_pearsonr
except Exception:  # pragma: no cover - fallback when scipy is unavailable
    scipy_pearsonr = None


# ── PARAMETERS ────────────────────────────────────────────────
LSH_DIR = Path("data/processed/lsh")
METRICS_DIR = Path("data/processed/metrics")
FIGURES_DIR = Path("figures/02_metrics")
QUALITY_AUDIT_PATH = Path("data/processed/quality_audit/startup_meeting_quality_audit_v2.csv")
SAMPLE_INVENTORY_AUDIT_PATH = Path("data/processed/sample_inventory_audit.csv")
README_PATH = Path("analysis/02_metrics/README.md")

ENTROPY_WINDOW = 61     # seconds, centered
PCT_DET_WINDOW = 301    # seconds, centered
RMSE_WINDOW = 30        # seconds, prior lookback window
RMSE_DELTA_N = 20       # prediction horizon in seconds
RMSE_EPSILON = 3.0      # noise radius in %DET units
STEP_SIZE = 1           # seconds
MIN_DIAG_LENGTH = 2     # minimum diagonal length for %DET
MIN_RMSE_NEIGHBORS = 3
POOLED_CORR_SAMPLE_FRAC = 0.20
SCATTER_SAMPLE_FRAC = 0.05
RNG_SEED = 42
# ──────────────────────────────────────────────────────────────

sns.set_theme(style="whitegrid", context="talk")


def fisher_pvalue(r: float, n: int) -> float:
    if n < 4 or np.isnan(r):
        return float("nan")
    if abs(r) >= 1.0:
        return 0.0
    z = 0.5 * math.log((1 + r) / (1 - r)) * math.sqrt(max(n - 3, 1))
    return math.erfc(abs(z) / math.sqrt(2.0))


def compute_pearson(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, int]:
    mask = np.isfinite(x) & np.isfinite(y)
    n = int(mask.sum())
    if n < 3:
        return float("nan"), float("nan"), n
    x_valid = x[mask]
    y_valid = y[mask]
    if np.std(x_valid) == 0 or np.std(y_valid) == 0:
        return float("nan"), float("nan"), n
    if scipy_pearsonr is not None:
        r, p = scipy_pearsonr(x_valid, y_valid)
        return float(r), float(p), n
    r = float(np.corrcoef(x_valid, y_valid)[0, 1])
    p = fisher_pvalue(r, n)
    return r, p, n


def run_lengths_of_ones(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return np.empty(0, dtype=np.int64)
    padded = np.concatenate(([0], arr.astype(np.int8), [0]))
    diff = np.diff(padded)
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    return ends - starts


def pct_det_for_window(symbols: np.ndarray) -> float:
    n = int(symbols.size)
    if n < 2:
        return 0.0
    recurrent_points = 0
    diagonal_points = 0
    for offset in range(1, n):
        matches = (symbols[:-offset] == symbols[offset:])
        recurrent_points += int(matches.sum())
        if matches.any():
            lengths = run_lengths_of_ones(matches)
            if lengths.size:
                diagonal_points += int(lengths[lengths >= MIN_DIAG_LENGTH].sum())
    if recurrent_points == 0:
        return 0.0
    return float(100.0 * diagonal_points / recurrent_points)


def shannon_entropy_from_counts(counts: np.ndarray) -> float:
    total = counts.sum()
    if total <= 0:
        return 0.0
    probs = counts[counts > 0] / total
    return float(-(probs * np.log2(probs)).sum())


def compute_entropy_series(speakers: np.ndarray) -> np.ndarray:
    n = len(speakers)
    unique_speakers = np.unique(speakers)
    speaker_to_idx = {speaker: idx for idx, speaker in enumerate(unique_speakers)}
    mapped = np.array([speaker_to_idx[s] for s in speakers], dtype=np.int64)
    counts = np.zeros(len(unique_speakers), dtype=np.int64)
    result = np.zeros(n, dtype=float)

    half_window = ENTROPY_WINDOW // 2
    left = 0
    right = -1

    for t in range(n):
        new_left = max(0, t - half_window)
        new_right = min(n - 1, t + half_window)

        while left < new_left:
            counts[mapped[left]] -= 1
            left += 1
        while left > new_left:
            left -= 1
            counts[mapped[left]] += 1
        while right < new_right:
            right += 1
            counts[mapped[right]] += 1
        while right > new_right:
            counts[mapped[right]] -= 1
            right -= 1

        result[t] = shannon_entropy_from_counts(counts)

    return result


def compute_pct_det_series(speakers: np.ndarray) -> np.ndarray:
    n = len(speakers)
    result = np.zeros(n, dtype=float)
    half_window = PCT_DET_WINDOW // 2
    for t in range(n):
        start = max(0, t - half_window)
        end = min(n, t + half_window + 1)
        result[t] = pct_det_for_window(speakers[start:end])
    return result


def compute_rmse_series(pct_det: np.ndarray) -> np.ndarray:
    n = len(pct_det)
    rmse = np.full(n, np.nan, dtype=float)
    horizon = RMSE_DELTA_N
    for t in range(n):
        if not np.isfinite(pct_det[t]):
            continue
        if t + horizon >= n:
            continue
        obs = pct_det[t + 1:t + horizon + 1]
        if not np.all(np.isfinite(obs)):
            continue

        start = max(0, t - RMSE_WINDOW)
        candidate_idx = np.arange(start, t)
        if candidate_idx.size == 0:
            continue
        candidate_idx = candidate_idx[candidate_idx + horizon < n]
        if candidate_idx.size == 0:
            continue
        neighbor_mask = np.isfinite(pct_det[candidate_idx]) & (np.abs(pct_det[candidate_idx] - pct_det[t]) <= RMSE_EPSILON)
        neighbors = candidate_idx[neighbor_mask]
        if neighbors.size < MIN_RMSE_NEIGHBORS:
            continue
        trajectories = np.vstack([pct_det[s + 1:s + horizon + 1] for s in neighbors])
        if trajectories.shape[0] < MIN_RMSE_NEIGHBORS:
            continue
        mean_prediction = np.nanmean(trajectories, axis=0)
        if not np.all(np.isfinite(mean_prediction)):
            continue
        rmse[t] = float(np.sqrt(np.mean((mean_prediction - obs) ** 2)))
    return rmse


def edge_window_flags(n: int) -> np.ndarray:
    entropy_half = ENTROPY_WINDOW // 2
    pct_det_half = PCT_DET_WINDOW // 2
    flags = np.zeros(n, dtype=bool)
    for t in range(n):
        entropy_edge = (t - entropy_half < 0) or (t + entropy_half >= n)
        pct_det_edge = (t - pct_det_half < 0) or (t + pct_det_half >= n)
        flags[t] = entropy_edge or pct_det_edge
    return flags


def validate_meeting(meeting_id: str, lsh_df: pd.DataFrame, metrics_df: pd.DataFrame) -> Dict[str, object]:
    speaker_count = int(lsh_df["speaker_id"].nunique())
    entropy_upper = math.log2(max(speaker_count, 1))
    validation = {
        "meeting_id": meeting_id,
        "row_count_matches": len(lsh_df) == len(metrics_df),
        "negative_rmse_count": int((metrics_df["rmse"].dropna() < 0).sum()),
        "entropy_in_range": bool(((metrics_df["entropy"] >= -1e-9) & (metrics_df["entropy"] <= entropy_upper + 1e-9)).all()),
        "pct_det_in_range": bool(((metrics_df["pct_det"] >= -1e-9) & (metrics_df["pct_det"] <= 100 + 1e-9)).all()),
        "nan_rmse_seconds": int(metrics_df["rmse"].isna().sum()),
        "n_speakers": speaker_count,
        "entropy_upper_bound": entropy_upper,
    }
    return validation


def write_summary_readme(summary_df: pd.DataFrame, correlations_df: pd.DataFrame) -> None:
    overall_entropy_mean = summary_df["entropy_mean"].mean()
    overall_entropy_sd = summary_df["entropy_mean"].std(ddof=1)
    overall_pct_det_mean = summary_df["pct_det_mean"].mean()
    overall_pct_det_sd = summary_df["pct_det_mean"].std(ddof=1)
    overall_rmse_mean = summary_df["rmse_mean"].mean()
    overall_rmse_sd = summary_df["rmse_mean"].std(ddof=1)
    overall_rmse_coverage = summary_df["rmse_coverage_pct"].mean()

    include_count = int((summary_df["quality_label"] == "include").sum())
    caution_count = int((summary_df["quality_label"] == "include_with_caution").sum())

    pooled = correlations_df[correlations_df["method"] == "pooled_sample_20pct"].copy()
    pooled_map = {
        (row["metric_x"], row["metric_y"]): row["r"]
        for _, row in pooled.iterrows()
    }

    text = f"""# 02_metrics

This directory contains the code and documentation for the **metrics** stage of the reproducible analysis pipeline.

## Step 2 — Dynamic Communication Metrics

Input:  `data/processed/lsh/*_lsh.csv`
Output: `data/processed/metrics/*_metrics.csv`
        `data/processed/metrics/metrics_summary.csv`
        `data/processed/metrics/metrics_correlations.csv`

### Parameters

Entropy:  window = 61s (centered), Shannon H
%DET:     window = 301s (centered), min diagonal = 2
RMSE:     lookback window = 30s, Δn = 20s, ε = 3.0 %DET units

### Results

Meetings processed: 34 ({include_count} include, {caution_count} include_with_caution)
Entropy: mean = {overall_entropy_mean:.3f} (SD = {overall_entropy_sd:.3f})
%DET:    mean = {overall_pct_det_mean:.3f} (SD = {overall_pct_det_sd:.3f})
RMSE:    mean = {overall_rmse_mean:.3f} (SD = {overall_rmse_sd:.3f}), coverage = {overall_rmse_coverage:.2f}%
Correlations (pooled): entropy–pct_det r={pooled_map.get(('entropy', 'pct_det'), float('nan')):.3f}, entropy–rmse r={pooled_map.get(('entropy', 'rmse'), float('nan')):.3f}, pct_det–rmse r={pooled_map.get(('pct_det', 'rmse'), float('nan')):.3f}

### Files

- `main.py` computes second-level dynamic communication metrics for all retained meetings.
- `data/processed/sample_inventory_audit.csv` stores the Step 2 quality labels copied from the quality audit.
- `data/processed/metrics/` stores per-meeting metrics plus the summary and correlation tables.
- `figures/02_metrics/` stores pooled distributions, an example time series panel, between-meeting variability plots, and the metric scatter matrix.
"""
    README_PATH.write_text(text)


def save_distribution_figure(long_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(22, 6), constrained_layout=True)
    for ax, metric in zip(axes, ["entropy", "pct_det", "rmse"]):
        plot_df = long_df[[metric, "quality_label"]].dropna().rename(columns={metric: "value"})
        sns.histplot(
            data=plot_df,
            x="value",
            hue="quality_label",
            kde=True,
            stat="density",
            common_norm=False,
            alpha=0.35,
            ax=ax,
        )
        ax.set_title(metric)
        ax.set_xlabel(metric)
        ax.set_ylabel("Density")
    fig.suptitle("Metric distributions pooled across all meetings", y=1.02)
    fig.savefig(FIGURES_DIR / "metric_distributions.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_timeseries_example(example_df: pd.DataFrame, meeting_id: str) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(20, 10), sharex=True, constrained_layout=True)
    for ax, metric, color in zip(axes, ["entropy", "pct_det", "rmse"], ["#1f77b4", "#2ca02c", "#d62728"]):
        ax.plot(example_df["second"], example_df[metric], color=color, linewidth=1.2)
        ax.set_ylabel(metric)
        ax.set_title(f"{meeting_id} — {metric}")
    axes[-1].set_xlabel("Second")
    fig.suptitle(f"Example dynamic communication metrics: {meeting_id}", y=1.02)
    fig.savefig(FIGURES_DIR / "metric_timeseries_example.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_between_meeting_variability(summary_df: pd.DataFrame) -> None:
    melted = summary_df.melt(
        id_vars=["meeting_id", "quality_label"],
        value_vars=["entropy_mean", "pct_det_mean", "rmse_mean"],
        var_name="metric",
        value_name="value",
    )
    fig, axes = plt.subplots(1, 3, figsize=(22, 7), constrained_layout=True)
    for ax, metric in zip(axes, ["entropy_mean", "pct_det_mean", "rmse_mean"]):
        plot_df = melted[melted["metric"] == metric].copy()
        sns.boxplot(data=plot_df, x="quality_label", y="value", ax=ax, color="white")
        sns.stripplot(data=plot_df, x="quality_label", y="value", hue="quality_label", dodge=False, ax=ax, size=8)
        ax.set_title(metric)
        ax.set_xlabel("")
        ax.set_ylabel("Per-meeting mean")
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()
    fig.suptitle("Between-meeting variability in metric means", y=1.02)
    fig.savefig(FIGURES_DIR / "between_meeting_variability.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_correlation_matrix(long_df: pd.DataFrame, corr_annotations: Dict[Tuple[str, str], float]) -> None:
    sample_df = long_df[["entropy", "pct_det", "rmse"]].dropna().sample(frac=SCATTER_SAMPLE_FRAC, random_state=RNG_SEED)
    g = sns.PairGrid(sample_df, vars=["entropy", "pct_det", "rmse"], diag_sharey=False)
    g.map_diag(sns.histplot, kde=True, color="#4c72b0")
    g.map_lower(sns.scatterplot, s=12, alpha=0.35, color="#4c72b0")
    g.map_upper(sns.scatterplot, s=12, alpha=0.35, color="#4c72b0")

    for i, metric_y in enumerate(g.y_vars):
        for j, metric_x in enumerate(g.x_vars):
            ax = g.axes[i, j]
            if i != j:
                key = tuple(sorted((metric_x, metric_y)))
                r = corr_annotations.get(key)
                if r is not None and np.isfinite(r):
                    ax.text(0.05, 0.95, f"r = {r:.3f}", transform=ax.transAxes, ha="left", va="top", fontsize=12,
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7))
    g.fig.suptitle("Metric correlations across pooled meeting-seconds", y=1.02)
    g.fig.savefig(FIGURES_DIR / "metric_correlations.png", dpi=200, bbox_inches="tight")
    plt.close(g.fig)


def main() -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    audit_df = pd.read_csv(QUALITY_AUDIT_PATH)
    audit_df = audit_df.rename(columns={"final_label": "quality_label"}) if "final_label" in audit_df.columns and "quality_label" not in audit_df.columns else audit_df
    if "quality_label" not in audit_df.columns:
        audit_df["quality_label"] = audit_df["final_label"]
    audit_df.to_csv(SAMPLE_INVENTORY_AUDIT_PATH, index=False)
    quality_map = audit_df.set_index("meeting_id")["quality_label"].to_dict()

    lsh_files = sorted([p for p in LSH_DIR.glob("*_lsh.csv") if p.name not in {"lsh_summary.csv", "lsh_validation.csv"}])
    if len(lsh_files) != 34:
        raise ValueError(f"Expected 34 LSH meeting files, found {len(lsh_files)}")

    rng = np.random.default_rng(RNG_SEED)
    summary_rows: List[Dict[str, object]] = []
    correlation_rows: List[Dict[str, object]] = []
    validation_rows: List[Dict[str, object]] = []
    pooled_frames: List[pd.DataFrame] = []
    representative_include: Tuple[str, pd.DataFrame] | None = None

    for lsh_file in lsh_files:
        meeting_id = lsh_file.name.replace("_lsh.csv", "")
        quality_label = quality_map.get(meeting_id)
        if quality_label is None:
            raise KeyError(f"Meeting {meeting_id} missing from audit file")

        lsh_df = pd.read_csv(lsh_file)
        lsh_df = lsh_df[["second", "speaker_id"]].copy()
        lsh_df["second"] = lsh_df["second"].astype(int)
        lsh_df["speaker_id"] = lsh_df["speaker_id"].astype(int)
        speakers = lsh_df["speaker_id"].to_numpy(dtype=np.int64)

        entropy = compute_entropy_series(speakers)
        pct_det = compute_pct_det_series(speakers)
        rmse = compute_rmse_series(pct_det)
        edges = edge_window_flags(len(lsh_df))

        metrics_df = pd.DataFrame({
            "second": lsh_df["second"].astype(int),
            "entropy": entropy.astype(float),
            "pct_det": pct_det.astype(float),
            "rmse": rmse.astype(float),
            "edge_window": edges.astype(bool),
        })
        metrics_df.to_csv(METRICS_DIR / f"{meeting_id}_metrics.csv", index=False)

        validation = validate_meeting(meeting_id, lsh_df, metrics_df)
        validation_rows.append(validation)
        print(
            f"{meeting_id}: rows_match={validation['row_count_matches']} | negative_rmse={validation['negative_rmse_count']} | "
            f"entropy_in_range={validation['entropy_in_range']} | pct_det_in_range={validation['pct_det_in_range']} | "
            f"nan_rmse_seconds={validation['nan_rmse_seconds']}"
        )

        summary_rows.append({
            "meeting_id": meeting_id,
            "quality_label": quality_label,
            "entropy_mean": float(metrics_df["entropy"].mean()),
            "entropy_sd": float(metrics_df["entropy"].std(ddof=1)),
            "entropy_min": float(metrics_df["entropy"].min()),
            "entropy_max": float(metrics_df["entropy"].max()),
            "pct_det_mean": float(metrics_df["pct_det"].mean()),
            "pct_det_sd": float(metrics_df["pct_det"].std(ddof=1)),
            "pct_det_min": float(metrics_df["pct_det"].min()),
            "pct_det_max": float(metrics_df["pct_det"].max()),
            "rmse_mean": float(metrics_df["rmse"].mean(skipna=True)),
            "rmse_sd": float(metrics_df["rmse"].std(ddof=1, skipna=True)),
            "rmse_min": float(metrics_df["rmse"].min(skipna=True)) if metrics_df["rmse"].notna().any() else float("nan"),
            "rmse_max": float(metrics_df["rmse"].max(skipna=True)) if metrics_df["rmse"].notna().any() else float("nan"),
            "rmse_coverage_pct": float(metrics_df["rmse"].notna().mean() * 100.0),
        })

        for metric_x, metric_y in [("entropy", "pct_det"), ("entropy", "rmse"), ("pct_det", "rmse")]:
            r, p, n = compute_pearson(metrics_df[metric_x].to_numpy(), metrics_df[metric_y].to_numpy())
            correlation_rows.append({
                "method": "per_meeting",
                "meeting_id": meeting_id,
                "metric_x": metric_x,
                "metric_y": metric_y,
                "r": r,
                "p_value": p,
                "n": n,
            })

        pooled_meeting_df = metrics_df.assign(meeting_id=meeting_id, quality_label=quality_label)
        pooled_frames.append(pooled_meeting_df)

        if representative_include is None and quality_label == "include":
            representative_include = (meeting_id, pooled_meeting_df.copy())

    summary_df = pd.DataFrame(summary_rows).sort_values("meeting_id").reset_index(drop=True)
    summary_df.to_csv(METRICS_DIR / "metrics_summary.csv", index=False)

    validation_df = pd.DataFrame(validation_rows).sort_values("meeting_id").reset_index(drop=True)
    validation_df.to_csv(METRICS_DIR / "metrics_validation.csv", index=False)

    pooled_df = pd.concat(pooled_frames, ignore_index=True)
    pooled_complete = pooled_df[["entropy", "pct_det", "rmse"]].dropna()
    sample_n = max(3, int(len(pooled_complete) * POOLED_CORR_SAMPLE_FRAC))
    pooled_sample = pooled_complete.sample(n=sample_n, random_state=RNG_SEED) if len(pooled_complete) > sample_n else pooled_complete.copy()

    for metric_x, metric_y in [("entropy", "pct_det"), ("entropy", "rmse"), ("pct_det", "rmse")]:
        r, p, n = compute_pearson(pooled_sample[metric_x].to_numpy(), pooled_sample[metric_y].to_numpy())
        correlation_rows.append({
            "method": "pooled_sample_20pct",
            "meeting_id": "ALL",
            "metric_x": metric_x,
            "metric_y": metric_y,
            "r": r,
            "p_value": p,
            "n": n,
        })

    per_meeting_df = pd.DataFrame(correlation_rows)
    averaged_rows: List[Dict[str, object]] = []
    for metric_x, metric_y in [("entropy", "pct_det"), ("entropy", "rmse"), ("pct_det", "rmse")]:
        subset = per_meeting_df[
            (per_meeting_df["method"] == "per_meeting")
            & (per_meeting_df["metric_x"] == metric_x)
            & (per_meeting_df["metric_y"] == metric_y)
        ]
        r_values = subset["r"].to_numpy(dtype=float)
        finite = np.isfinite(r_values)
        avg_r = float(np.nanmean(r_values)) if finite.any() else float("nan")
        avg_p = fisher_pvalue(avg_r, int(finite.sum())) if finite.sum() >= 4 else float("nan")
        averaged_rows.append({
            "method": "per_meeting_average",
            "meeting_id": "ALL",
            "metric_x": metric_x,
            "metric_y": metric_y,
            "r": avg_r,
            "p_value": avg_p,
            "n": int(finite.sum()),
        })

    correlations_df = pd.concat([per_meeting_df, pd.DataFrame(averaged_rows)], ignore_index=True)
    correlations_df.to_csv(METRICS_DIR / "metrics_correlations.csv", index=False)

    save_distribution_figure(pooled_df)
    if representative_include is None:
        raise RuntimeError("No representative include meeting found")
    save_timeseries_example(representative_include[1], representative_include[0])
    save_between_meeting_variability(summary_df)

    pooled_corr_annot = {}
    for _, row in correlations_df[correlations_df["method"] == "pooled_sample_20pct"].iterrows():
        pooled_corr_annot[tuple(sorted((row["metric_x"], row["metric_y"])))] = float(row["r"])
    save_correlation_matrix(pooled_df, pooled_corr_annot)

    write_summary_readme(summary_df, correlations_df)

    print("\nStep 2 complete.")
    print(f"Processed meetings: {len(summary_df)}")
    print(f"Include meetings: {(summary_df['quality_label'] == 'include').sum()}")
    print(f"Include with caution meetings: {(summary_df['quality_label'] == 'include_with_caution').sum()}")


if __name__ == "__main__":
    main()
