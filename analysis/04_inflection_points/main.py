from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path("/home/ubuntu/small-groups-comm-metrics")
METRICS_DIR = BASE_DIR / "data/processed/metrics"
OUTPUT_DIR = BASE_DIR / "data/processed/inflection_points"
FIGURES_DIR = BASE_DIR / "figures/04_inflection_points"
README_PATH = BASE_DIR / "analysis/04_inflection_points/README.md"

METRICS = ["entropy", "pct_det", "rmse"]
SHIFT_WINDOW = 30
SMOOTH_WINDOW = 15
MIN_SEPARATION = 60
MIN_VALID_METRICS = 2
THRESHOLD_QUANTILE = 0.95
THRESHOLD_Z = 2.5
TOP_N_PER_MEETING = 10


def robust_scale(values: pd.Series) -> float:
    clean = values.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
    if clean.empty:
        return 1.0
    median = float(clean.median())
    mad = float((clean - median).abs().median())
    if np.isfinite(mad) and mad > 1e-9:
        return 1.4826 * mad
    std = float(clean.std(ddof=0))
    if np.isfinite(std) and std > 1e-9:
        return std
    return 1.0


def smooth_metric(series: pd.Series) -> pd.Series:
    return series.astype(float).rolling(SMOOTH_WINDOW, center=True, min_periods=5).median()


def compute_shift_signal(series: pd.Series) -> pd.Series:
    left = series.shift(1).rolling(SHIFT_WINDOW, min_periods=max(5, SHIFT_WINDOW // 3)).mean()
    right = series[::-1].shift(1).rolling(SHIFT_WINDOW, min_periods=max(5, SHIFT_WINDOW // 3)).mean()[::-1]
    return right - left


def local_maxima(mask: np.ndarray, values: np.ndarray) -> np.ndarray:
    out = np.zeros_like(mask, dtype=bool)
    idx = np.where(mask)[0]
    for i in idx:
        left = values[i - 1] if i - 1 >= 0 else -np.inf
        right = values[i + 1] if i + 1 < len(values) else -np.inf
        if values[i] >= left and values[i] >= right:
            out[i] = True
    return out


def select_peaks(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    score = df["composite_score"].to_numpy(dtype=float)
    valid_mask = np.isfinite(score) & (score >= threshold)
    maxima_mask = local_maxima(valid_mask, score)
    peak_idx = np.where(maxima_mask)[0]
    if peak_idx.size == 0:
        return df.iloc[[]].copy()

    order = peak_idx[np.argsort(score[peak_idx])[::-1]]
    selected: List[int] = []
    for idx in order:
        second = int(df.iloc[idx]["second"])
        if all(abs(second - int(df.iloc[j]["second"])) >= MIN_SEPARATION for j in selected):
            selected.append(int(idx))

    selected = sorted(selected, key=lambda j: float(df.iloc[j]["composite_score"]), reverse=True)
    peaks = df.iloc[selected].copy()
    peaks["rank_within_meeting"] = np.arange(1, len(peaks) + 1)
    return peaks


def top_contributors(row: pd.Series) -> str:
    parts = []
    for metric in METRICS:
        value = row.get(f"{metric}_shift_z", np.nan)
        raw = row.get(f"{metric}_shift", np.nan)
        if pd.notna(value):
            direction = "increase" if pd.notna(raw) and raw > 0 else "decrease"
            parts.append((abs(float(value)), f"{metric}:{direction}"))
    if not parts:
        return ""
    parts.sort(reverse=True)
    return "; ".join(label for _, label in parts[:3])


def process_meeting(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    meeting_id = path.name.replace("_metrics.csv", "")
    df = pd.read_csv(path)
    if "second" not in df.columns:
        raise ValueError(f"Missing 'second' column in {path.name}")

    score_df = df[["second", "edge_window"] + METRICS].copy()
    valid_metric_counts = np.zeros(len(score_df), dtype=int)
    z_columns: List[str] = []

    for metric in METRICS:
        raw = score_df[metric].astype(float)
        smoothed = smooth_metric(raw)
        shift = compute_shift_signal(smoothed)
        valid = raw.notna() & smoothed.notna() & shift.notna() & (~score_df["edge_window"].astype(bool))
        scale = robust_scale(shift.loc[valid])
        z = (shift / scale).where(valid)
        score_df[f"{metric}_smoothed"] = smoothed
        score_df[f"{metric}_shift"] = shift.where(valid)
        score_df[f"{metric}_shift_z"] = z
        valid_metric_counts += z.notna().to_numpy(dtype=int)
        z_columns.append(f"{metric}_shift_z")

    abs_z = score_df[z_columns].abs()
    score_df["valid_metric_count"] = valid_metric_counts
    score_df["composite_score"] = abs_z.mean(axis=1, skipna=True)
    score_df.loc[score_df["valid_metric_count"] < MIN_VALID_METRICS, "composite_score"] = np.nan

    clean_scores = score_df["composite_score"].dropna()
    if clean_scores.empty:
        threshold = np.nan
    else:
        median = float(clean_scores.median())
        scale = robust_scale(clean_scores)
        adaptive = median + THRESHOLD_Z * scale
        quantile = float(clean_scores.quantile(THRESHOLD_QUANTILE))
        threshold = max(quantile, adaptive)

    score_df["threshold"] = threshold
    if np.isfinite(threshold):
        peaks = select_peaks(score_df, float(threshold))
    else:
        peaks = score_df.iloc[[]].copy()

    if peaks.empty:
        score_df["is_candidate"] = False
        score_df["rank_within_meeting"] = np.nan
    else:
        score_df["is_candidate"] = score_df["second"].isin(peaks["second"])
        ranks = peaks.set_index("second")["rank_within_meeting"].to_dict()
        score_df["rank_within_meeting"] = score_df["second"].map(ranks)

    candidate_cols = [
        "second",
        "composite_score",
        "threshold",
        "rank_within_meeting",
        "valid_metric_count",
    ] + [f"{metric}_shift" for metric in METRICS] + [f"{metric}_shift_z" for metric in METRICS]
    peaks = peaks[candidate_cols].copy()
    peaks.insert(0, "meeting_id", meeting_id)
    peaks["top_contributors"] = peaks.apply(top_contributors, axis=1)

    meeting_summary = {
        "meeting_id": meeting_id,
        "n_seconds": int(len(score_df)),
        "valid_seconds": int(score_df["composite_score"].notna().sum()),
        "candidate_count": int(len(peaks)),
        "threshold": float(threshold) if np.isfinite(threshold) else np.nan,
        "max_composite_score": float(clean_scores.max()) if not clean_scores.empty else np.nan,
        "median_composite_score": float(clean_scores.median()) if not clean_scores.empty else np.nan,
    }
    return score_df, peaks, meeting_summary


def save_meeting_figure(score_df: pd.DataFrame, peaks: pd.DataFrame, meeting_id: str) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(18, 10), sharex=True, constrained_layout=True)
    colors = {"entropy": "#1f77b4", "pct_det": "#2ca02c", "rmse": "#d62728"}

    for ax, metric in zip(axes[:3], METRICS):
        ax.plot(score_df["second"], score_df[metric], color=colors[metric], linewidth=1.0, alpha=0.35, label=f"{metric} raw")
        ax.plot(score_df["second"], score_df[f"{metric}_smoothed"], color=colors[metric], linewidth=1.3, label=f"{metric} smoothed")
        for second in peaks["second"].tolist():
            ax.axvline(second, color="#444444", linewidth=0.8, alpha=0.35)
        ax.set_ylabel(metric)
        ax.legend(loc="upper right", frameon=False)

    axes[3].plot(score_df["second"], score_df["composite_score"], color="#6a3d9a", linewidth=1.4, label="composite score")
    if peaks.shape[0] > 0 and np.isfinite(float(peaks["threshold"].iloc[0])):
        axes[3].axhline(float(peaks["threshold"].iloc[0]), color="#ff7f00", linestyle="--", linewidth=1.2, label="candidate threshold")
    for _, row in peaks.iterrows():
        second = int(row["second"])
        axes[3].axvline(second, color="#444444", linewidth=0.9, alpha=0.45)
        axes[3].text(second, float(row["composite_score"]), f"#{int(row['rank_within_meeting'])}", fontsize=8, ha="left", va="bottom")
    axes[3].set_ylabel("score")
    axes[3].set_xlabel("Second")
    axes[3].legend(loc="upper right", frameon=False)

    fig.suptitle(f"Step 04 candidate inflection points: {meeting_id}", y=1.02)
    fig.savefig(FIGURES_DIR / f"{meeting_id}_inflection_points.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def update_readme(summary_df: pd.DataFrame, candidates_df: pd.DataFrame) -> None:
    meeting_count = int(summary_df.shape[0])
    total_candidates = int(candidates_df.shape[0])
    mean_candidates = float(summary_df["candidate_count"].mean()) if not summary_df.empty else float("nan")
    median_candidates = float(summary_df["candidate_count"].median()) if not summary_df.empty else float("nan")
    max_candidates = int(summary_df["candidate_count"].max()) if not summary_df.empty else 0

    if total_candidates > 0:
        top_row = candidates_df.sort_values(["composite_score", "meeting_id"], ascending=[False, True]).iloc[0]
        top_text = (
            f"Highest-scoring candidate: `{top_row['meeting_id']}` at second `{int(top_row['second'])}` "
            f"with composite score `{float(top_row['composite_score']):.3f}`."
        )
    else:
        top_text = "No candidates exceeded the adaptive threshold."

    readme = f"""# 04_inflection_points

This directory contains the code and documentation for the **inflection points** stage of the reproducible analysis pipeline.

## Step 4 — Candidate Inflection Points

Input: `data/processed/metrics/*_metrics.csv`  
Output: `data/processed/inflection_points/`, `figures/04_inflection_points/`

### Detection logic

For each meeting, the pipeline smooths the second-by-second Entropy, %DET, and RMSE series with a centered rolling median (`{SMOOTH_WINDOW}` s). It then computes a **local shift signal** for each metric as the difference between the mean of the following `{SHIFT_WINDOW}` seconds and the mean of the preceding `{SHIFT_WINDOW}` seconds. These shift signals are robustly standardized within meeting, combined into a composite magnitude score, and filtered so that a second must have at least `{MIN_VALID_METRICS}` valid metrics to be eligible.

Candidate inflection points are selected as local maxima of the composite score that exceed an **adaptive threshold** defined as the larger of the meeting-specific `{THRESHOLD_QUANTILE:.0%}` quantile and `median + {THRESHOLD_Z:.1f} × robust scale`. Nearby peaks are merged with a minimum separation of `{MIN_SEPARATION}` seconds.

### Results

Meetings processed: `{meeting_count}`  
Total candidate inflection points: `{total_candidates}`  
Mean candidates per meeting: `{mean_candidates:.2f}`  
Median candidates per meeting: `{median_candidates:.2f}`  
Maximum candidates in a single meeting: `{max_candidates}`

{top_text}

### Files

| File | Purpose |
|---|---|
| `main.py` | Detects candidate inflection points from the dynamic metric series and exports summary tables plus diagnostic figures. |
| `data/processed/inflection_points/meeting_inflection_summary.csv` | One row per meeting with thresholds, valid coverage, and candidate counts. |
| `data/processed/inflection_points/all_inflection_candidates.csv` | Pooled table of candidate seconds, scores, and top contributing metrics across meetings. |
| `data/processed/inflection_points/*_inflection_scores.csv` | Per-second inflection scores and candidate flags for each meeting. |
| `figures/04_inflection_points/*_inflection_points.png` | Meeting-level diagnostic panels showing raw metrics, smoothed metrics, and selected candidate points. |
"""
    README_PATH.write_text(readme)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    metric_files = sorted(METRICS_DIR.glob("*_metrics.csv"))
    if not metric_files:
        raise FileNotFoundError(f"No metrics files found in {METRICS_DIR}")

    all_candidates: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, float]] = []

    for path in metric_files:
        score_df, peaks, meeting_summary = process_meeting(path)
        meeting_id = meeting_summary["meeting_id"]
        score_df.to_csv(OUTPUT_DIR / f"{meeting_id}_inflection_scores.csv", index=False)
        save_meeting_figure(score_df, peaks, meeting_id)
        all_candidates.append(peaks)
        summary_rows.append(meeting_summary)

    summary_df = pd.DataFrame(summary_rows).sort_values("meeting_id").reset_index(drop=True)
    candidates_df = pd.concat(all_candidates, ignore_index=True) if all_candidates else pd.DataFrame()

    summary_df.to_csv(OUTPUT_DIR / "meeting_inflection_summary.csv", index=False)
    candidates_df.to_csv(OUTPUT_DIR / "all_inflection_candidates.csv", index=False)
    update_readme(summary_df, candidates_df)


if __name__ == "__main__":
    main()
