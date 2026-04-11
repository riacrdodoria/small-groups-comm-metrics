from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path("/home/ubuntu/small-groups-comm-metrics")
CONV_DIR = BASE_DIR / "data/processed/convergent_validity"
FIG_DIR = BASE_DIR / "figures/03_convergent_validity/temporal_meetings_v2"
OUT_DIR = CONV_DIR / "temporal_comparison_v2"

METRICS = ["entropy", "pct_det", "rmse"]
LABELS = {
    "entropy": "Entropy",
    "pct_det": "%DET",
    "rmse": "RMSE",
}
COLORS = {
    "standard": "#1f77b4",
    "lsh_equivalent": "#d62728",
}


def significance_label(p_value: float) -> str:
    if pd.isna(p_value):
        return "n.s."
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return "n.s."


def load_inputs() -> Dict[str, pd.DataFrame]:
    standard = pd.read_csv(CONV_DIR / "metrics_standard_all.csv")
    lsh = pd.read_csv(CONV_DIR / "metrics_lsh_all.csv")
    corr = pd.read_csv(CONV_DIR / "convergent_validity_results.csv")
    inventory = pd.read_csv(CONV_DIR / "gorman_series_inventory.csv")
    return {
        "standard": standard,
        "lsh": lsh,
        "corr": corr,
        "inventory": inventory,
    }


def build_meeting_figure(team_id: str, merged: pd.DataFrame, corr_subset: pd.DataFrame, meta_row: pd.Series, output_path: Path) -> None:
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(16, 11), sharex=True, constrained_layout=True)
    fig.suptitle(
        f"Temporal metric comparison: {team_id} | {meta_row['domain']} | {meta_row['context']}\n"
        f"Original Gorman series vs. LSH-equivalent series",
        fontsize=16,
        fontweight="bold",
    )

    for ax, metric in zip(axes, METRICS):
        y_standard = merged[f"{metric}_standard"]
        y_lsh = merged[f"{metric}_lsh"]
        ax.plot(merged["second"], y_standard, color=COLORS["standard"], linewidth=1.2, alpha=0.9, label="Original")
        ax.plot(merged["second"], y_lsh, color=COLORS["lsh_equivalent"], linewidth=1.2, alpha=0.8, label="LSH-equivalent")

        row = corr_subset.loc[corr_subset["metric"] == metric].iloc[0]
        sig = significance_label(float(row["p_value"]))
        p_display = f"{float(row['p_value']):.3g}" if float(row["p_value"]) > 0 else "<1e-300"
        ax.set_title(
            f"{LABELS[metric]} | r = {float(row['r']):.3f} | p = {p_display} | sig. {sig}",
            fontsize=12,
        )
        ax.set_ylabel(LABELS[metric])
        ax.grid(True, alpha=0.25)
        ymin = np.nanmin(np.concatenate([y_standard.to_numpy(dtype=float), y_lsh.to_numpy(dtype=float)]))
        ymax = np.nanmax(np.concatenate([y_standard.to_numpy(dtype=float), y_lsh.to_numpy(dtype=float)]))
        if np.isfinite(ymin) and np.isfinite(ymax) and ymin != ymax:
            margin = (ymax - ymin) * 0.08
            ax.set_ylim(ymin - margin, ymax + margin)
        ax.legend(loc="upper right")

    axes[-1].set_xlabel("Second")
    footer = (
        f"Silence in original series = {float(meta_row['silence_pct']):.2f}% | "
        f"Duration = {int(meta_row['n_seconds']):,} seconds | File = {meta_row['source_file']}"
    )
    fig.text(0.5, 0.005, footer, ha="center", fontsize=10)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    inputs = load_inputs()
    standard = inputs["standard"]
    lsh = inputs["lsh"]
    corr = inputs["corr"]
    inventory = inputs["inventory"]
    if "status" in inventory.columns:
        inventory = inventory.loc[inventory["status"] == "processed"].copy()

    summary_rows: List[Dict[str, object]] = []
    report_lines: List[str] = []
    report_lines.append("# Temporal Comparison of Original vs. LSH-Equivalent Metrics\n")
    report_lines.append(
        "This report summarizes, for each meeting, the second-by-second comparison between the original Gorman metric series and the LSH-equivalent metric series. "
        "The correlation values below refer to paired temporal series within the same meeting.\n"
    )

    valid_team_ids = sorted(set(standard["team_id"].unique()) & set(inventory["team_id"].unique()))
    for team_id in valid_team_ids:
        standard_team = standard.loc[standard["team_id"] == team_id].copy()
        lsh_team = lsh.loc[lsh["team_id"] == team_id].copy()
        merged = standard_team.merge(
            lsh_team[["team_id", "second", "entropy", "pct_det", "rmse"]],
            on=["team_id", "second"],
            suffixes=("_standard", "_lsh"),
            how="inner",
        )
        corr_subset = corr.loc[corr["team_id"] == team_id].copy().sort_values("metric")
        meta_row = inventory.loc[inventory["team_id"] == team_id].iloc[0]

        figure_name = f"{team_id}_temporal_comparison.png"
        build_meeting_figure(team_id, merged, corr_subset, meta_row, FIG_DIR / figure_name)

        row: Dict[str, object] = {
            "team_id": team_id,
            "domain": meta_row["domain"],
            "context": meta_row["context"],
            "source_file": meta_row["source_file"],
            "n_seconds": int(meta_row["n_seconds"]),
            "silence_pct": float(meta_row["silence_pct"]),
            "figure_file": str((FIG_DIR / figure_name).relative_to(BASE_DIR)),
        }
        report_lines.append(f"## {team_id}\n")
        report_lines.append(
            f"**Domain:** {meta_row['domain']}  \n**Context:** {meta_row['context']}  \n"
            f"**Silence in original series:** {float(meta_row['silence_pct']):.2f}%  \n"
            f"**Temporal figure:** `{str((FIG_DIR / figure_name).relative_to(BASE_DIR))}`\n"
        )
        report_lines.append("| Metric | r | p-value | Sig. | Correlated? |\n|---|---:|---:|:---:|:---:|\n")
        for metric in METRICS:
            metric_row = corr_subset.loc[corr_subset["metric"] == metric].iloc[0]
            p_value = float(metric_row["p_value"])
            sig = significance_label(p_value)
            correlated = "Yes" if (float(metric_row["r"]) > 0 and p_value < 0.05) else "No"
            row[f"r_{metric}"] = float(metric_row["r"])
            row[f"p_{metric}"] = p_value
            row[f"sig_{metric}"] = sig
            row[f"correlated_{metric}"] = correlated
            p_display = f"{p_value:.3g}" if p_value > 0 else "<1e-300"
            report_lines.append(
                f"| {LABELS[metric]} | {float(metric_row['r']):.3f} | {p_display} | {sig} | {correlated} |\n"
            )
        report_lines.append("\n")
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows).sort_values(["domain", "team_id"])
    summary_df.to_csv(OUT_DIR / "meeting_temporal_correlation_summary.csv", index=False)
    (OUT_DIR / "meeting_temporal_correlation_summary.md").write_text("".join(report_lines))


if __name__ == "__main__":
    main()
