from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = Path("/home/ubuntu/small-groups-comm-metrics")
METRICS_DIR = BASE_DIR / "data/processed/metrics"
OUTPUT_DIR = BASE_DIR / "data/processed/inflection_points"
FIGURES_DIR = BASE_DIR / "figures/04_inflection_points"
AUDIT_PATH = BASE_DIR / "data/processed/sample_inventory_audit.csv"
README_PATH = BASE_DIR / "analysis/04_inflection_points/README.md"

ALPHA_LEVEL = 0.05
T_CRIT_QUANTILE = 0.95  # one-tailed alpha=0.05
MIN_PEAK_SEPARATION_SECONDS = 60
WINDOW_RADIUS = 30
MIN_WINDOW_VALID_SECONDS = 10
QUALITY_ORDER = ["include", "include_with_caution"]
QUALITY_COLORS = {"include": "#1f77b4", "include_with_caution": "#ff7f0e", "unknown": "#7f7f7f"}


def load_quality_labels() -> pd.DataFrame:
    audit = pd.read_csv(AUDIT_PATH)
    if "meeting_id" not in audit.columns or "quality_label" not in audit.columns:
        raise ValueError("sample_inventory_audit.csv must contain 'meeting_id' and 'quality_label' columns")
    return audit[["meeting_id", "quality_label"]].drop_duplicates(subset=["meeting_id"])


def clean_output_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    for path in OUTPUT_DIR.glob("*.csv"):
        path.unlink()
    for path in FIGURES_DIR.glob("*.png"):
        path.unlink()


def contiguous_runs(seconds: Iterable[int]) -> List[tuple[int, int]]:
    seconds = sorted(int(x) for x in seconds)
    if not seconds:
        return []
    runs: List[tuple[int, int]] = []
    start = seconds[0]
    previous = seconds[0]
    for second in seconds[1:]:
        if second == previous + 1:
            previous = second
            continue
        runs.append((start, previous))
        start = second
        previous = second
    runs.append((start, previous))
    return runs


def select_peaks_with_minimum_separation(events: List[Dict[str, float]], min_separation: int) -> List[Dict[str, float]]:
    if not events:
        return []
    ordered = sorted(events, key=lambda row: (-float(row["peak_rmse"]), int(row["peak_second"])))
    kept: List[Dict[str, float]] = []
    for event in ordered:
        peak_second = int(event["peak_second"])
        if all(abs(peak_second - int(existing["peak_second"])) >= min_separation for existing in kept):
            kept.append(event)
    kept.sort(key=lambda row: int(row["peak_second"]))
    return kept


def compute_window_mean(df: pd.DataFrame, metric: str, start_second: int, end_second: int) -> tuple[float, int]:
    mask = (
        (df["second"] >= start_second)
        & (df["second"] <= end_second)
        & (~df["edge_window"])
        & df[metric].notna()
    )
    subset = df.loc[mask, metric].astype(float)
    if subset.empty:
        return np.nan, 0
    return float(subset.mean()), int(subset.shape[0])


def process_meeting(path: Path, quality_lookup: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, float], pd.DataFrame]:
    meeting_id = path.name.replace("_metrics.csv", "")
    df = pd.read_csv(path)
    required_columns = {"second", "entropy", "pct_det", "rmse", "edge_window"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {sorted(missing)}")

    df = df.copy()
    df["second"] = pd.to_numeric(df["second"], errors="coerce")
    for metric in ["entropy", "pct_det", "rmse"]:
        df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df["edge_window"] = df["edge_window"].astype(str).str.lower().map({"true": True, "false": False})
    df["edge_window"] = df["edge_window"].fillna(False).astype(bool)
    df = df.dropna(subset=["second"]).sort_values("second").reset_index(drop=True)
    df["second"] = df["second"].astype(int)

    quality_match = quality_lookup.loc[quality_lookup["meeting_id"] == meeting_id, "quality_label"]
    quality_label = quality_match.iloc[0] if not quality_match.empty else "unknown"

    valid_rmse = df.loc[(~df["edge_window"]) & df["rmse"].notna(), "rmse"].astype(float)
    n_valid = int(valid_rmse.shape[0])
    meeting_duration_seconds = int(df["second"].max()) + 1 if not df.empty else 0

    if n_valid >= 2:
        rmse_mean = float(valid_rmse.mean())
        rmse_sd = float(valid_rmse.std(ddof=1))
        t_crit = float(stats.t.ppf(T_CRIT_QUANTILE, df=n_valid - 1))
        ucl = float(rmse_mean + t_crit * rmse_sd) if np.isfinite(rmse_sd) else np.nan
    else:
        rmse_mean = np.nan
        rmse_sd = np.nan
        t_crit = np.nan
        ucl = np.nan

    candidate_seconds = df.loc[(~df["edge_window"]) & df["rmse"].notna() & (df["rmse"] > ucl), "second"].tolist() if np.isfinite(ucl) else []
    runs = contiguous_runs(candidate_seconds)

    preliminary_events: List[Dict[str, float]] = []
    for onset_second, offset_second in runs:
        run_df = df.loc[(df["second"] >= onset_second) & (df["second"] <= offset_second) & df["rmse"].notna(), ["second", "rmse"]].copy()
        if run_df.empty:
            continue
        peak_row = run_df.sort_values(["rmse", "second"], ascending=[False, True]).iloc[0]
        preliminary_events.append(
            {
                "meeting_id": meeting_id,
                "onset_second": int(onset_second),
                "offset_second": int(offset_second),
                "peak_second": int(peak_row["second"]),
                "peak_rmse": float(peak_row["rmse"]),
                "alpha_level": ALPHA_LEVEL,
                "ucl": float(ucl) if np.isfinite(ucl) else np.nan,
                "temporal_position": float(int(peak_row["second"]) / meeting_duration_seconds) if meeting_duration_seconds > 0 else np.nan,
                "quality_label": quality_label,
            }
        )

    retained_events = select_peaks_with_minimum_separation(preliminary_events, MIN_PEAK_SEPARATION_SECONDS)

    entropy_sd = float(df.loc[(~df["edge_window"]) & df["entropy"].notna(), "entropy"].astype(float).std(ddof=1))
    pct_det_sd = float(df.loc[(~df["edge_window"]) & df["pct_det"].notna(), "pct_det"].astype(float).std(ddof=1))

    inflection_rows: List[Dict[str, float]] = []
    for event in retained_events:
        peak_second = int(event["peak_second"])
        pre_entropy, pre_entropy_n = compute_window_mean(df, "entropy", peak_second - WINDOW_RADIUS, peak_second - 1)
        post_entropy, post_entropy_n = compute_window_mean(df, "entropy", peak_second + 1, peak_second + WINDOW_RADIUS)
        pre_pct_det, pre_pct_det_n = compute_window_mean(df, "pct_det", peak_second - WINDOW_RADIUS, peak_second - 1)
        post_pct_det, post_pct_det_n = compute_window_mean(df, "pct_det", peak_second + 1, peak_second + WINDOW_RADIUS)

        delta_entropy = abs(post_entropy - pre_entropy) if np.isfinite(pre_entropy) and np.isfinite(post_entropy) else np.nan
        delta_pct_det = abs(post_pct_det - pre_pct_det) if np.isfinite(pre_pct_det) and np.isfinite(post_pct_det) else np.nan

        z_delta_entropy = delta_entropy / entropy_sd if np.isfinite(delta_entropy) and np.isfinite(entropy_sd) and entropy_sd > 0 else np.nan
        z_delta_pct_det = delta_pct_det / pct_det_sd if np.isfinite(delta_pct_det) and np.isfinite(pct_det_sd) and pct_det_sd > 0 else np.nan

        sufficient_windows = all(
            count >= MIN_WINDOW_VALID_SECONDS
            for count in [pre_entropy_n, post_entropy_n, pre_pct_det_n, post_pct_det_n]
        )
        combined_delta = (
            float(np.nanmean([z_delta_entropy, z_delta_pct_det]))
            if sufficient_windows and (np.isfinite(z_delta_entropy) or np.isfinite(z_delta_pct_det))
            else np.nan
        )

        inflection_rows.append(
            {
                **event,
                "combined_delta": combined_delta,
                "pre_entropy": pre_entropy,
                "post_entropy": post_entropy,
                "delta_entropy": delta_entropy,
                "z_delta_entropy": z_delta_entropy,
                "pre_pct_det": pre_pct_det,
                "post_pct_det": post_pct_det,
                "delta_pct_det": delta_pct_det,
                "z_delta_pct_det": z_delta_pct_det,
            }
        )

    inflections_df = pd.DataFrame(
        inflection_rows,
        columns=[
            "meeting_id",
            "onset_second",
            "offset_second",
            "peak_second",
            "peak_rmse",
            "alpha_level",
            "ucl",
            "temporal_position",
            "combined_delta",
            "pre_entropy",
            "post_entropy",
            "delta_entropy",
            "z_delta_entropy",
            "pre_pct_det",
            "post_pct_det",
            "delta_pct_det",
            "z_delta_pct_det",
            "quality_label",
        ],
    )

    summary_row = {
        "meeting_id": meeting_id,
        "quality_label": quality_label,
        "n_inflection_points": int(inflections_df.shape[0]),
        "mean_peak_rmse": float(inflections_df["peak_rmse"].mean()) if not inflections_df.empty else np.nan,
        "mean_combined_delta": float(inflections_df["combined_delta"].mean()) if not inflections_df.empty else np.nan,
        "mean_temporal_position": float(inflections_df["temporal_position"].mean()) if not inflections_df.empty else np.nan,
        "ucl": float(ucl) if np.isfinite(ucl) else np.nan,
        "meeting_duration_seconds": meeting_duration_seconds,
    }

    metadata_row = {
        "meeting_id": meeting_id,
        "quality_label": quality_label,
        "meeting_duration_seconds": meeting_duration_seconds,
        "valid_rmse_seconds": n_valid,
        "ucl": float(ucl) if np.isfinite(ucl) else np.nan,
        "rmse_mean": rmse_mean,
        "rmse_sd": rmse_sd,
        "t_crit": t_crit,
    }

    return inflections_df, summary_row, pd.DataFrame([metadata_row])


def save_rmse_ucl_distribution(valid_rmse_df: pd.DataFrame, metadata_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True, constrained_layout=True)
    for ax, quality_label in zip(axes, QUALITY_ORDER):
        subset = valid_rmse_df.loc[valid_rmse_df["quality_label"] == quality_label, "rmse"].astype(float)
        mean_ucl = metadata_df.loc[metadata_df["quality_label"] == quality_label, "ucl"].astype(float).mean()
        ax.hist(subset, bins=40, color=QUALITY_COLORS[quality_label], alpha=0.75, edgecolor="white")
        if np.isfinite(mean_ucl):
            ax.axvline(mean_ucl, color="#222222", linestyle="--", linewidth=1.5, label=f"mean UCL = {mean_ucl:.3f}")
            ax.legend(frameon=False, loc="upper right")
        ax.set_title(quality_label)
        ax.set_xlabel("RMSE")
        ax.set_ylabel("Per-second count")
    fig.suptitle("Pooled per-second RMSE distributions with mean UCL by quality label")
    fig.savefig(FIGURES_DIR / "rmse_ucl_distribution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_inflection_points_per_meeting(summary_df: pd.DataFrame) -> None:
    plot_df = summary_df.sort_values(["n_inflection_points", "meeting_id"], ascending=[False, True]).reset_index(drop=True)
    colors = [QUALITY_COLORS.get(label, QUALITY_COLORS["unknown"]) for label in plot_df["quality_label"]]

    fig, ax = plt.subplots(figsize=(18, 7), constrained_layout=True)
    ax.bar(plot_df["meeting_id"], plot_df["n_inflection_points"], color=colors)
    ax.set_ylabel("Inflection points")
    ax.set_xlabel("Meeting ID")
    ax.set_title("Inflection points per meeting")
    ax.tick_params(axis="x", rotation=90)

    legend_handles = [
        plt.Line2D([0], [0], color=QUALITY_COLORS[label], lw=8, label=label)
        for label in QUALITY_ORDER
        if label in plot_df["quality_label"].values
    ]
    if "unknown" in plot_df["quality_label"].values:
        legend_handles.append(plt.Line2D([0], [0], color=QUALITY_COLORS["unknown"], lw=8, label="unknown"))
    if legend_handles:
        ax.legend(handles=legend_handles, frameon=False)

    fig.savefig(FIGURES_DIR / "inflection_points_per_meeting.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_temporal_position_distribution(inflections_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    values = inflections_df["temporal_position"].astype(float).dropna()
    ax.hist(values, bins=20, color="#6a3d9a", alpha=0.8, edgecolor="white")
    ax.set_xlabel("Temporal position")
    ax.set_ylabel("Inflection point count")
    ax.set_title("Distribution of retained inflection-point temporal positions")
    fig.savefig(FIGURES_DIR / "temporal_position_distribution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_combined_delta_distribution(inflections_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    values = inflections_df["combined_delta"].astype(float).dropna()
    ax.hist(values, bins=20, color="#2ca02c", alpha=0.8, edgecolor="white")
    mean_value = float(values.mean()) if not values.empty else np.nan
    if np.isfinite(mean_value):
        ax.axvline(mean_value, color="#222222", linestyle="--", linewidth=1.5, label=f"mean = {mean_value:.3f}")
        ax.legend(frameon=False)
    ax.set_xlabel("Combined delta")
    ax.set_ylabel("Inflection point count")
    ax.set_title("Distribution of combined_delta across retained inflection points")
    fig.savefig(FIGURES_DIR / "combined_delta_distribution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_example_meeting_panel(metric_paths: List[Path], inflections_df: pd.DataFrame, summary_df: pd.DataFrame, metadata_df: pd.DataFrame) -> str:
    if summary_df.empty:
        raise ValueError("No meetings available to create example_meeting_panel.png")

    median_count = float(summary_df["n_inflection_points"].median())
    example_row = summary_df.assign(distance=(summary_df["n_inflection_points"] - median_count).abs()).sort_values(
        ["distance", "n_inflection_points", "meeting_id"], ascending=[True, True, True]
    ).iloc[0]
    meeting_id = str(example_row["meeting_id"])

    metrics_path = next(path for path in metric_paths if path.name == f"{meeting_id}_metrics.csv")
    df = pd.read_csv(metrics_path)
    df["second"] = pd.to_numeric(df["second"], errors="coerce")
    for metric in ["entropy", "pct_det", "rmse"]:
        df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df = df.dropna(subset=["second"]).sort_values("second").reset_index(drop=True)
    df["minute"] = df["second"] / 60.0

    retained = inflections_df.loc[inflections_df["meeting_id"] == meeting_id].copy()
    ucl = float(metadata_df.loc[metadata_df["meeting_id"] == meeting_id, "ucl"].iloc[0])

    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True, constrained_layout=True)
    metric_specs = [
        ("entropy", "#1f77b4", "Entropy"),
        ("pct_det", "#2ca02c", "%DET"),
        ("rmse", "#d62728", "RMSE"),
    ]

    for ax, (metric, color, label) in zip(axes, metric_specs):
        ax.plot(df["minute"], df[metric], color=color, linewidth=1.2)
        for peak_second in retained["peak_second"].tolist():
            ax.axvline(float(peak_second) / 60.0, color="#b22222", linestyle="-", linewidth=1.0, alpha=0.8)
        if metric == "rmse" and np.isfinite(ucl):
            ax.axhline(ucl, color="#222222", linestyle="--", linewidth=1.2, label=f"UCL = {ucl:.3f}")
            ax.legend(frameon=False, loc="upper right")
        ax.set_ylabel(label)

    axes[-1].set_xlabel("Time (minutes)")
    fig.suptitle(f"Example meeting panel: {meeting_id}")
    fig.savefig(FIGURES_DIR / "example_meeting_panel.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return meeting_id


def format_console_report(summary_df: pd.DataFrame, inflections_df: pd.DataFrame, metadata_df: pd.DataFrame) -> str:
    meetings_processed = int(summary_df.shape[0])
    total_inflection_points = int(inflections_df.shape[0])
    mean_per_meeting = float(summary_df["n_inflection_points"].mean()) if not summary_df.empty else np.nan
    sd_per_meeting = float(summary_df["n_inflection_points"].std(ddof=1)) if summary_df.shape[0] > 1 else 0.0
    min_points = int(summary_df["n_inflection_points"].min()) if not summary_df.empty else 0
    max_points = int(summary_df["n_inflection_points"].max()) if not summary_df.empty else 0
    mean_peak_rmse = float(inflections_df["peak_rmse"].mean()) if not inflections_df.empty else np.nan
    mean_ucl = float(metadata_df["ucl"].mean()) if not metadata_df.empty else np.nan
    mean_combined_delta = float(inflections_df["combined_delta"].mean()) if not inflections_df.empty else np.nan
    sd_combined_delta = float(inflections_df["combined_delta"].std(ddof=1)) if inflections_df["combined_delta"].notna().sum() > 1 else 0.0
    meetings_with_zero = int((summary_df["n_inflection_points"] == 0).sum()) if not summary_df.empty else 0

    include_mean = float(summary_df.loc[summary_df["quality_label"] == "include", "n_inflection_points"].mean())
    caution_mean = float(summary_df.loc[summary_df["quality_label"] == "include_with_caution", "n_inflection_points"].mean())

    return "\n".join(
        [
            "=== Step 4: Inflection Point Identification (UCL method) ===",
            "Algorithm: RMSE > UCL (t-distribution, alpha=0.05, per-meeting)",
            f"Meetings processed: {meetings_processed}",
            f"Total inflection points: {total_inflection_points}",
            f"Mean per meeting: {mean_per_meeting:.2f} (SD={sd_per_meeting:.2f}, range={min_points}–{max_points})",
            f"Mean peak RMSE: {mean_peak_rmse:.3f}",
            f"Mean UCL: {mean_ucl:.3f}",
            f"Mean combined_delta: {mean_combined_delta:.3f} (SD={sd_combined_delta:.3f})",
            f"Meetings with 0 inflection points: {meetings_with_zero}",
            f"  include meetings — mean {include_mean:.2f} inflection points",
            f"  include_with_caution — mean {caution_mean:.2f} inflection points",
        ]
    )


def main() -> None:
    clean_output_directories()
    quality_lookup = load_quality_labels()
    metric_paths = sorted(METRICS_DIR.glob("*_metrics.csv"))
    if not metric_paths:
        raise FileNotFoundError(f"No metrics files found in {METRICS_DIR}")

    all_inflections: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, float]] = []
    metadata_rows: List[pd.DataFrame] = []
    valid_rmse_rows: List[pd.DataFrame] = []

    for path in metric_paths:
        inflections_df, summary_row, metadata_df = process_meeting(path, quality_lookup)
        meeting_id = summary_row["meeting_id"]

        raw_df = pd.read_csv(path)
        raw_df["rmse"] = pd.to_numeric(raw_df["rmse"], errors="coerce")
        raw_df["edge_window"] = raw_df["edge_window"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False).astype(bool)
        valid_rmse = raw_df.loc[(~raw_df["edge_window"]) & raw_df["rmse"].notna(), ["rmse"]].copy()
        valid_rmse.insert(0, "meeting_id", meeting_id)
        valid_rmse.insert(1, "quality_label", summary_row["quality_label"])
        valid_rmse_rows.append(valid_rmse)

        all_inflections.append(inflections_df)
        summary_rows.append(summary_row)
        metadata_rows.append(metadata_df)

    inflections_all = pd.concat(all_inflections, ignore_index=True) if all_inflections else pd.DataFrame()
    if "quality_label" in inflections_all.columns:
        inflections_output = inflections_all.drop(columns=["quality_label"])
    else:
        inflections_output = inflections_all
    summary_df = pd.DataFrame(summary_rows).sort_values("meeting_id").reset_index(drop=True)
    metadata_df = pd.concat(metadata_rows, ignore_index=True).sort_values("meeting_id").reset_index(drop=True)
    valid_rmse_df = pd.concat(valid_rmse_rows, ignore_index=True)

    inflections_output.to_csv(OUTPUT_DIR / "inflection_points.csv", index=False)
    summary_df.to_csv(OUTPUT_DIR / "inflection_points_summary.csv", index=False)

    save_rmse_ucl_distribution(valid_rmse_df, metadata_df)
    save_inflection_points_per_meeting(summary_df)
    save_temporal_position_distribution(inflections_all)
    save_combined_delta_distribution(inflections_all)
    example_meeting_id = save_example_meeting_panel(metric_paths, inflections_all, summary_df, metadata_df)

    console_report = format_console_report(summary_df, inflections_all, metadata_df)
    print(console_report)
    print(f"Example meeting panel source: {example_meeting_id}")


if __name__ == "__main__":
    main()
