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
METRIC_SPECS = {
    "rmse": {"label": "RMSE", "color": "#d62728"},
    "entropy": {"label": "Entropy", "color": "#1f77b4"},
    "pct_det": {"label": "%DET", "color": "#2ca02c"},
}


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


def compute_control_statistics(series: pd.Series) -> Dict[str, float]:
    valid = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    n_valid = int(valid.shape[0])
    if n_valid >= 2:
        mean_value = float(valid.mean())
        sd_value = float(valid.std(ddof=1))
        t_crit = float(stats.t.ppf(T_CRIT_QUANTILE, df=n_valid - 1))
        ucl = float(mean_value + t_crit * sd_value) if np.isfinite(sd_value) else np.nan
        lcl = float(mean_value - t_crit * sd_value) if np.isfinite(sd_value) else np.nan
    else:
        mean_value = np.nan
        sd_value = np.nan
        t_crit = np.nan
        ucl = np.nan
        lcl = np.nan
    return {
        "n_valid": n_valid,
        "mean": mean_value,
        "sd": sd_value,
        "t_crit": t_crit,
        "ucl": ucl,
        "lcl": lcl,
    }


def build_metric_rows(df: pd.DataFrame, meeting_id: str, quality_label: str) -> List[pd.DataFrame]:
    metric_frames: List[pd.DataFrame] = []
    valid_mask = ~df["edge_window"]
    for metric in METRIC_SPECS:
        subset = df.loc[valid_mask & df[metric].notna(), [metric]].copy()
        subset.insert(0, "meeting_id", meeting_id)
        subset.insert(1, "quality_label", quality_label)
        subset.insert(2, "metric", metric)
        subset = subset.rename(columns={metric: "value"})
        metric_frames.append(subset)
    return metric_frames


def process_meeting(path: Path, quality_lookup: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, float], pd.DataFrame, List[pd.DataFrame]]:
    meeting_id = path.name.replace("_metrics.csv", "")
    df = pd.read_csv(path)
    required_columns = {"second", "entropy", "pct_det", "rmse", "edge_window"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {sorted(missing)}")

    df = df.copy()
    df["second"] = pd.to_numeric(df["second"], errors="coerce")
    for metric in METRIC_SPECS:
        df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df["edge_window"] = df["edge_window"].astype(str).str.lower().map({"true": True, "false": False})
    df["edge_window"] = df["edge_window"].fillna(False).astype(bool)
    df = df.dropna(subset=["second"]).sort_values("second").reset_index(drop=True)
    df["second"] = df["second"].astype(int)

    quality_match = quality_lookup.loc[quality_lookup["meeting_id"] == meeting_id, "quality_label"]
    quality_label = quality_match.iloc[0] if not quality_match.empty else "unknown"
    meeting_duration_seconds = int(df["second"].max()) + 1 if not df.empty else 0

    valid_mask = ~df["edge_window"]
    control_stats = {
        metric: compute_control_statistics(df.loc[valid_mask, metric])
        for metric in METRIC_SPECS
    }

    rmse_stats = control_stats["rmse"]
    rmse_ucl = float(rmse_stats["ucl"]) if np.isfinite(rmse_stats["ucl"]) else np.nan
    candidate_seconds = (
        df.loc[valid_mask & df["rmse"].notna() & (df["rmse"] > rmse_ucl), "second"].tolist()
        if np.isfinite(rmse_ucl)
        else []
    )
    runs = contiguous_runs(candidate_seconds)

    preliminary_events: List[Dict[str, float]] = []
    for onset_second, offset_second in runs:
        run_df = df.loc[
            (df["second"] >= onset_second) & (df["second"] <= offset_second) & df["rmse"].notna(),
            ["second", "rmse"],
        ].copy()
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
                "ucl": rmse_ucl,
                "temporal_position": float(int(peak_row["second"]) / meeting_duration_seconds) if meeting_duration_seconds > 0 else np.nan,
                "quality_label": quality_label,
            }
        )

    retained_events = select_peaks_with_minimum_separation(preliminary_events, MIN_PEAK_SEPARATION_SECONDS)

    inflection_rows: List[Dict[str, float]] = []
    for event in retained_events:
        peak_second = int(event["peak_second"])
        peak_values = df.loc[df["second"] == peak_second, ["entropy", "pct_det", "rmse"]].iloc[0]

        metric_windows: Dict[str, Dict[str, float]] = {}
        for metric in METRIC_SPECS:
            pre_mean, pre_n = compute_window_mean(df, metric, peak_second - WINDOW_RADIUS, peak_second - 1)
            post_mean, post_n = compute_window_mean(df, metric, peak_second + 1, peak_second + WINDOW_RADIUS)
            delta_value = abs(post_mean - pre_mean) if np.isfinite(pre_mean) and np.isfinite(post_mean) else np.nan
            metric_sd = float(control_stats[metric]["sd"]) if np.isfinite(control_stats[metric]["sd"]) else np.nan
            z_delta = delta_value / metric_sd if np.isfinite(delta_value) and np.isfinite(metric_sd) and metric_sd > 0 else np.nan
            sufficient_windows = pre_n >= MIN_WINDOW_VALID_SECONDS and post_n >= MIN_WINDOW_VALID_SECONDS
            metric_windows[metric] = {
                "pre_mean": pre_mean,
                "post_mean": post_mean,
                "pre_n": pre_n,
                "post_n": post_n,
                "delta": delta_value,
                "z_delta": z_delta,
                "sufficient_windows": sufficient_windows,
            }

        entropy_value = float(peak_values["entropy"]) if np.isfinite(peak_values["entropy"]) else np.nan
        pct_det_value = float(peak_values["pct_det"]) if np.isfinite(peak_values["pct_det"]) else np.nan
        entropy_ucl = float(control_stats["entropy"]["ucl"]) if np.isfinite(control_stats["entropy"]["ucl"]) else np.nan
        entropy_lcl = float(control_stats["entropy"]["lcl"]) if np.isfinite(control_stats["entropy"]["lcl"]) else np.nan
        pct_det_ucl = float(control_stats["pct_det"]["ucl"]) if np.isfinite(control_stats["pct_det"]["ucl"]) else np.nan
        pct_det_lcl = float(control_stats["pct_det"]["lcl"]) if np.isfinite(control_stats["pct_det"]["lcl"]) else np.nan

        entropy_exceeds_ucl = bool(np.isfinite(entropy_value) and np.isfinite(entropy_ucl) and entropy_value > entropy_ucl)
        entropy_below_lcl = bool(np.isfinite(entropy_value) and np.isfinite(entropy_lcl) and entropy_value < entropy_lcl)
        entropy_outside_limits = bool(entropy_exceeds_ucl or entropy_below_lcl)
        pct_det_exceeds_ucl = bool(np.isfinite(pct_det_value) and np.isfinite(pct_det_ucl) and pct_det_value > pct_det_ucl)
        pct_det_below_lcl = bool(np.isfinite(pct_det_value) and np.isfinite(pct_det_lcl) and pct_det_value < pct_det_lcl)
        pct_det_outside_limits = bool(pct_det_exceeds_ucl or pct_det_below_lcl)

        entropy_excess_over_ucl = (
            float(entropy_value - entropy_ucl)
            if np.isfinite(entropy_value) and np.isfinite(entropy_ucl)
            else np.nan
        )
        pct_det_excess_over_ucl = (
            float(pct_det_value - pct_det_ucl)
            if np.isfinite(pct_det_value) and np.isfinite(pct_det_ucl)
            else np.nan
        )
        rmse_excess_over_ucl = float(event["peak_rmse"] - event["ucl"]) if np.isfinite(event["ucl"]) else np.nan

        entropy_sd = float(control_stats["entropy"]["sd"]) if np.isfinite(control_stats["entropy"]["sd"]) else np.nan
        pct_det_sd = float(control_stats["pct_det"]["sd"]) if np.isfinite(control_stats["pct_det"]["sd"]) else np.nan
        rmse_sd = float(control_stats["rmse"]["sd"]) if np.isfinite(control_stats["rmse"]["sd"]) else np.nan

        entropy_excess_z = (
            float(max(entropy_excess_over_ucl, 0.0) / entropy_sd)
            if np.isfinite(entropy_excess_over_ucl) and np.isfinite(entropy_sd) and entropy_sd > 0
            else np.nan
        )
        pct_det_excess_z = (
            float(max(pct_det_excess_over_ucl, 0.0) / pct_det_sd)
            if np.isfinite(pct_det_excess_over_ucl) and np.isfinite(pct_det_sd) and pct_det_sd > 0
            else np.nan
        )
        rmse_excess_z = (
            float(max(rmse_excess_over_ucl, 0.0) / rmse_sd)
            if np.isfinite(rmse_excess_over_ucl) and np.isfinite(rmse_sd) and rmse_sd > 0
            else np.nan
        )

        entropy_pct_det_windows_ok = all(
            metric_windows[metric]["sufficient_windows"] for metric in ["entropy", "pct_det"]
        )
        combined_delta = (
            float(np.nanmean([metric_windows["entropy"]["z_delta"], metric_windows["pct_det"]["z_delta"]]))
            if entropy_pct_det_windows_ok
            and (
                np.isfinite(metric_windows["entropy"]["z_delta"])
                or np.isfinite(metric_windows["pct_det"]["z_delta"])
            )
            else np.nan
        )

        valid_v2_components = [
            metric_windows[metric]["z_delta"]
            for metric in ["rmse", "entropy", "pct_det"]
            if metric_windows[metric]["sufficient_windows"] and np.isfinite(metric_windows[metric]["z_delta"])
        ]
        combined_delta_v2 = float(np.mean(valid_v2_components)) if valid_v2_components else np.nan

        inflection_rows.append(
            {
                **event,
                "combined_delta": combined_delta,
                "combined_delta_v2": combined_delta_v2,
                "pre_entropy": metric_windows["entropy"]["pre_mean"],
                "post_entropy": metric_windows["entropy"]["post_mean"],
                "delta_entropy": metric_windows["entropy"]["delta"],
                "z_delta_entropy": metric_windows["entropy"]["z_delta"],
                "pre_pct_det": metric_windows["pct_det"]["pre_mean"],
                "post_pct_det": metric_windows["pct_det"]["post_mean"],
                "delta_pct_det": metric_windows["pct_det"]["delta"],
                "z_delta_pct_det": metric_windows["pct_det"]["z_delta"],
                "pre_rmse": metric_windows["rmse"]["pre_mean"],
                "post_rmse": metric_windows["rmse"]["post_mean"],
                "delta_rmse": metric_windows["rmse"]["delta"],
                "z_delta_rmse": metric_windows["rmse"]["z_delta"],
                "peak_entropy": entropy_value,
                "entropy_ucl": entropy_ucl,
                "entropy_lcl": entropy_lcl,
                "entropy_exceeds_ucl": entropy_exceeds_ucl,
                "entropy_below_lcl": entropy_below_lcl,
                "entropy_outside_limits": entropy_outside_limits,
                "entropy_excess_over_ucl": entropy_excess_over_ucl,
                "entropy_excess_z": entropy_excess_z,
                "peak_pct_det": pct_det_value,
                "pct_det_ucl": pct_det_ucl,
                "pct_det_lcl": pct_det_lcl,
                "pct_det_exceeds_ucl": pct_det_exceeds_ucl,
                "pct_det_below_lcl": pct_det_below_lcl,
                "pct_det_outside_limits": pct_det_outside_limits,
                "pct_det_excess_over_ucl": pct_det_excess_over_ucl,
                "pct_det_excess_z": pct_det_excess_z,
                "rmse_excess_over_ucl": rmse_excess_over_ucl,
                "rmse_excess_z": rmse_excess_z,
                "auxiliary_ucl_corroboration": int(entropy_outside_limits or pct_det_outside_limits),
                "quality_label": quality_label,
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
            "combined_delta_v2",
            "pre_entropy",
            "post_entropy",
            "delta_entropy",
            "z_delta_entropy",
            "pre_pct_det",
            "post_pct_det",
            "delta_pct_det",
            "z_delta_pct_det",
            "pre_rmse",
            "post_rmse",
            "delta_rmse",
            "z_delta_rmse",
            "peak_entropy",
            "entropy_ucl",
            "entropy_lcl",
            "entropy_exceeds_ucl",
            "entropy_below_lcl",
            "entropy_outside_limits",
            "entropy_excess_over_ucl",
            "entropy_excess_z",
            "peak_pct_det",
            "pct_det_ucl",
            "pct_det_lcl",
            "pct_det_exceeds_ucl",
            "pct_det_below_lcl",
            "pct_det_outside_limits",
            "pct_det_excess_over_ucl",
            "pct_det_excess_z",
            "rmse_excess_over_ucl",
            "rmse_excess_z",
            "auxiliary_ucl_corroboration",
            "quality_label",
        ],
    )

    summary_row = {
        "meeting_id": meeting_id,
        "quality_label": quality_label,
        "n_inflection_points": int(inflections_df.shape[0]),
        "mean_peak_rmse": float(inflections_df["peak_rmse"].mean()) if not inflections_df.empty else np.nan,
        "mean_peak_entropy": float(inflections_df["peak_entropy"].mean()) if not inflections_df.empty else np.nan,
        "mean_peak_pct_det": float(inflections_df["peak_pct_det"].mean()) if not inflections_df.empty else np.nan,
        "mean_combined_delta": float(inflections_df["combined_delta"].mean()) if not inflections_df.empty else np.nan,
        "mean_combined_delta_v2": float(inflections_df["combined_delta_v2"].mean()) if not inflections_df.empty else np.nan,
        "mean_temporal_position": float(inflections_df["temporal_position"].mean()) if not inflections_df.empty else np.nan,
        "rmse_ucl": rmse_ucl,
        "entropy_ucl": entropy_ucl if retained_events else float(control_stats["entropy"]["ucl"]),
        "pct_det_ucl": pct_det_ucl if retained_events else float(control_stats["pct_det"]["ucl"]),
        "n_entropy_peak_exceeds_ucl": int(inflections_df["entropy_exceeds_ucl"].sum()) if not inflections_df.empty else 0,
        "n_entropy_peak_outside_limits": int(inflections_df["entropy_outside_limits"].sum()) if not inflections_df.empty else 0,
        "n_pct_det_peak_exceeds_ucl": int(inflections_df["pct_det_exceeds_ucl"].sum()) if not inflections_df.empty else 0,
        "n_pct_det_peak_outside_limits": int(inflections_df["pct_det_outside_limits"].sum()) if not inflections_df.empty else 0,
        "n_auxiliary_ucl_corroborated": int(inflections_df["auxiliary_ucl_corroboration"].sum()) if not inflections_df.empty else 0,
        "meeting_duration_seconds": meeting_duration_seconds,
    }

    metadata_row = {
        "meeting_id": meeting_id,
        "quality_label": quality_label,
        "meeting_duration_seconds": meeting_duration_seconds,
        "valid_rmse_seconds": int(control_stats["rmse"]["n_valid"]),
        "valid_entropy_seconds": int(control_stats["entropy"]["n_valid"]),
        "valid_pct_det_seconds": int(control_stats["pct_det"]["n_valid"]),
        "rmse_ucl": rmse_ucl,
        "rmse_lcl": float(control_stats["rmse"]["lcl"]) if np.isfinite(control_stats["rmse"]["lcl"]) else np.nan,
        "rmse_mean": float(control_stats["rmse"]["mean"]) if np.isfinite(control_stats["rmse"]["mean"]) else np.nan,
        "rmse_sd": rmse_sd,
        "entropy_ucl": float(control_stats["entropy"]["ucl"]) if np.isfinite(control_stats["entropy"]["ucl"]) else np.nan,
        "entropy_lcl": float(control_stats["entropy"]["lcl"]) if np.isfinite(control_stats["entropy"]["lcl"]) else np.nan,
        "entropy_mean": float(control_stats["entropy"]["mean"]) if np.isfinite(control_stats["entropy"]["mean"]) else np.nan,
        "entropy_sd": entropy_sd,
        "pct_det_ucl": float(control_stats["pct_det"]["ucl"]) if np.isfinite(control_stats["pct_det"]["ucl"]) else np.nan,
        "pct_det_lcl": float(control_stats["pct_det"]["lcl"]) if np.isfinite(control_stats["pct_det"]["lcl"]) else np.nan,
        "pct_det_mean": float(control_stats["pct_det"]["mean"]) if np.isfinite(control_stats["pct_det"]["mean"]) else np.nan,
        "pct_det_sd": pct_det_sd,
        "t_crit": float(control_stats["rmse"]["t_crit"]) if np.isfinite(control_stats["rmse"]["t_crit"]) else np.nan,
    }

    metric_rows = build_metric_rows(df, meeting_id, quality_label)
    return inflections_df, summary_row, pd.DataFrame([metadata_row]), metric_rows


def save_metric_ucl_distributions(valid_metric_df: pd.DataFrame, metadata_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), sharey="row", constrained_layout=True)
    for row_idx, quality_label in enumerate(QUALITY_ORDER):
        for col_idx, metric in enumerate(METRIC_SPECS):
            ax = axes[row_idx, col_idx]
            metric_subset = valid_metric_df.loc[
                (valid_metric_df["quality_label"] == quality_label) & (valid_metric_df["metric"] == metric),
                "value",
            ].astype(float)
            mean_ucl = metadata_df.loc[metadata_df["quality_label"] == quality_label, f"{metric}_ucl"].astype(float).mean()
            ax.hist(
                metric_subset,
                bins=40,
                color=METRIC_SPECS[metric]["color"],
                alpha=0.75,
                edgecolor="white",
            )
            if np.isfinite(mean_ucl):
                ax.axvline(mean_ucl, color="#222222", linestyle="--", linewidth=1.5, label=f"mean UCL = {mean_ucl:.3f}")
                ax.legend(frameon=False, loc="upper right")
            ax.set_title(f"{quality_label} — {METRIC_SPECS[metric]['label']}")
            ax.set_xlabel(METRIC_SPECS[metric]["label"])
            ax.set_ylabel("Per-second count")
    fig.suptitle("Pooled per-second metric distributions with mean UCL by quality label")
    fig.savefig(FIGURES_DIR / "metric_ucl_distributions.png", dpi=180, bbox_inches="tight")
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
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
    for ax, column, title, color in [
        (axes[0], "combined_delta", "combined_delta (Entropy + %DET)", "#2ca02c"),
        (axes[1], "combined_delta_v2", "combined_delta_v2 (RMSE + Entropy + %DET)", "#17becf"),
    ]:
        values = inflections_df[column].astype(float).dropna()
        ax.hist(values, bins=20, color=color, alpha=0.8, edgecolor="white")
        mean_value = float(values.mean()) if not values.empty else np.nan
        if np.isfinite(mean_value):
            ax.axvline(mean_value, color="#222222", linestyle="--", linewidth=1.5, label=f"mean = {mean_value:.3f}")
            ax.legend(frameon=False)
        ax.set_xlabel(column)
        ax.set_ylabel("Inflection point count")
        ax.set_title(title)
    fig.savefig(FIGURES_DIR / "combined_delta_distribution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_auxiliary_ucl_corroboration(summary_df: pd.DataFrame) -> None:
    plot_df = summary_df.copy()
    if plot_df.empty:
        return
    plot_df["entropy_share"] = np.where(
        plot_df["n_inflection_points"] > 0,
        plot_df["n_entropy_peak_outside_limits"] / plot_df["n_inflection_points"],
        0.0,
    )
    plot_df["pct_det_share"] = np.where(
        plot_df["n_inflection_points"] > 0,
        plot_df["n_pct_det_peak_outside_limits"] / plot_df["n_inflection_points"],
        0.0,
    )
    plot_df = plot_df.sort_values(["entropy_share", "pct_det_share", "meeting_id"], ascending=[False, False, True]).reset_index(drop=True)

    x = np.arange(plot_df.shape[0])
    width = 0.38
    fig, ax = plt.subplots(figsize=(18, 7), constrained_layout=True)
    ax.bar(x - width / 2, plot_df["entropy_share"], width=width, color=METRIC_SPECS["entropy"]["color"], label="Entropy outside-limits share")
    ax.bar(x + width / 2, plot_df["pct_det_share"], width=width, color=METRIC_SPECS["pct_det"]["color"], label="%DET outside-limits share")
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["meeting_id"], rotation=90)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of RMSE peaks outside auxiliary control limits")
    ax.set_xlabel("Meeting ID")
    ax.set_title("Auxiliary entropy and %DET control-limit corroboration of retained RMSE peaks")
    ax.legend(frameon=False)
    fig.savefig(FIGURES_DIR / "auxiliary_ucl_corroboration.png", dpi=180, bbox_inches="tight")
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
    for metric in METRIC_SPECS:
        df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df["edge_window"] = df["edge_window"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False).astype(bool)
    df = df.dropna(subset=["second"]).sort_values("second").reset_index(drop=True)
    df["minute"] = df["second"] / 60.0

    retained = inflections_df.loc[inflections_df["meeting_id"] == meeting_id].copy()
    meta = metadata_df.loc[metadata_df["meeting_id"] == meeting_id].iloc[0]

    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True, constrained_layout=True)
    for ax, metric in zip(axes, ["entropy", "pct_det", "rmse"]):
        ax.plot(df["minute"], df[metric], color=METRIC_SPECS[metric]["color"], linewidth=1.2)
        for peak_second in retained["peak_second"].tolist():
            ax.axvline(float(peak_second) / 60.0, color="#b22222", linestyle="-", linewidth=1.0, alpha=0.8)
        ucl = float(meta[f"{metric}_ucl"]) if np.isfinite(meta[f"{metric}_ucl"]) else np.nan
        lcl = float(meta[f"{metric}_lcl"]) if np.isfinite(meta[f"{metric}_lcl"]) else np.nan
        if np.isfinite(ucl):
            ax.axhline(ucl, color="#222222", linestyle="--", linewidth=1.2, label=f"UCL = {ucl:.3f}")
        if np.isfinite(lcl):
            ax.axhline(lcl, color="#555555", linestyle=":", linewidth=1.2, label=f"LCL = {lcl:.3f}")
        if np.isfinite(ucl) or np.isfinite(lcl):
            ax.legend(frameon=False, loc="upper right")
        ax.set_ylabel(METRIC_SPECS[metric]["label"])

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
    mean_rmse_ucl = float(metadata_df["rmse_ucl"].mean()) if not metadata_df.empty else np.nan
    mean_entropy_ucl = float(metadata_df["entropy_ucl"].mean()) if not metadata_df.empty else np.nan
    mean_pct_det_ucl = float(metadata_df["pct_det_ucl"].mean()) if not metadata_df.empty else np.nan
    mean_combined_delta = float(inflections_df["combined_delta"].mean()) if not inflections_df.empty else np.nan
    mean_combined_delta_v2 = float(inflections_df["combined_delta_v2"].mean()) if not inflections_df.empty else np.nan
    sd_combined_delta = float(inflections_df["combined_delta"].std(ddof=1)) if inflections_df["combined_delta"].notna().sum() > 1 else 0.0
    sd_combined_delta_v2 = float(inflections_df["combined_delta_v2"].std(ddof=1)) if inflections_df["combined_delta_v2"].notna().sum() > 1 else 0.0
    meetings_with_zero = int((summary_df["n_inflection_points"] == 0).sum()) if not summary_df.empty else 0
    entropy_corroborated = int(inflections_df["entropy_outside_limits"].sum()) if not inflections_df.empty else 0
    pct_det_corroborated = int(inflections_df["pct_det_outside_limits"].sum()) if not inflections_df.empty else 0
    any_auxiliary = int(inflections_df["auxiliary_ucl_corroboration"].sum()) if not inflections_df.empty else 0

    include_mean = float(summary_df.loc[summary_df["quality_label"] == "include", "n_inflection_points"].mean())
    caution_mean = float(summary_df.loc[summary_df["quality_label"] == "include_with_caution", "n_inflection_points"].mean())

    return "\n".join(
        [
            "=== Step 4: Inflection Point Identification (extended UCL method) ===",
            "Primary detector: RMSE > UCL (t-distribution, alpha=0.05, per-meeting)",
            "Auxiliary diagnostics: entropy UCL, %DET UCL, and expanded combined_delta_v2",
            f"Meetings processed: {meetings_processed}",
            f"Total inflection points: {total_inflection_points}",
            f"Mean per meeting: {mean_per_meeting:.2f} (SD={sd_per_meeting:.2f}, range={min_points}–{max_points})",
            f"Mean peak RMSE: {mean_peak_rmse:.3f}",
            f"Mean RMSE UCL: {mean_rmse_ucl:.3f}",
            f"Mean entropy UCL: {mean_entropy_ucl:.3f}",
            f"Mean %DET UCL: {mean_pct_det_ucl:.3f}",
            f"Mean combined_delta: {mean_combined_delta:.3f} (SD={sd_combined_delta:.3f})",
            f"Mean combined_delta_v2: {mean_combined_delta_v2:.3f} (SD={sd_combined_delta_v2:.3f})",
            f"Auxiliary corroboration counts (outside entropy/%DET control limits) — entropy: {entropy_corroborated}, %DET: {pct_det_corroborated}, either: {any_auxiliary}",
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
    valid_metric_rows: List[pd.DataFrame] = []

    for path in metric_paths:
        inflections_df, summary_row, metadata_df, metric_row_frames = process_meeting(path, quality_lookup)
        all_inflections.append(inflections_df)
        summary_rows.append(summary_row)
        metadata_rows.append(metadata_df)
        valid_metric_rows.extend(metric_row_frames)

    inflections_all = pd.concat(all_inflections, ignore_index=True) if all_inflections else pd.DataFrame()
    if "quality_label" in inflections_all.columns:
        inflections_output = inflections_all.drop(columns=["quality_label"])
    else:
        inflections_output = inflections_all
    summary_df = pd.DataFrame(summary_rows).sort_values("meeting_id").reset_index(drop=True)
    metadata_df = pd.concat(metadata_rows, ignore_index=True).sort_values("meeting_id").reset_index(drop=True)
    valid_metric_df = pd.concat(valid_metric_rows, ignore_index=True)

    inflections_output.to_csv(OUTPUT_DIR / "inflection_points.csv", index=False)
    summary_df.to_csv(OUTPUT_DIR / "inflection_points_summary.csv", index=False)
    metadata_df.to_csv(OUTPUT_DIR / "inflection_point_metadata.csv", index=False)

    save_metric_ucl_distributions(valid_metric_df, metadata_df)
    save_inflection_points_per_meeting(summary_df)
    save_temporal_position_distribution(inflections_all)
    save_combined_delta_distribution(inflections_all)
    save_auxiliary_ucl_corroboration(summary_df)
    example_meeting_id = save_example_meeting_panel(metric_paths, inflections_all, summary_df, metadata_df)

    console_report = format_console_report(summary_df, inflections_all, metadata_df)
    print(console_report)
    print(f"Example meeting panel source: {example_meeting_id}")


if __name__ == "__main__":
    main()
