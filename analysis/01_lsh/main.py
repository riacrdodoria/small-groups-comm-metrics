#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data" / "anonymized" / "startup"
OUTPUT_DIR = ROOT / "data" / "processed" / "lsh"
FIGURES_DIR = ROOT / "figures" / "01_lsh"
SUMMARY_PATH = OUTPUT_DIR / "lsh_summary.csv"
VALIDATION_PATH = OUTPUT_DIR / "lsh_validation.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Last-Speaker-Holds (LSH) 1 Hz time series from anonymized startup meetings.")
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing per-meeting outputs.")
    return parser.parse_args()


def load_input(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.shape[1] != 2:
        raise ValueError(f"{path.name} must have exactly 2 columns, found {df.shape[1]}")

    normalized_columns = [str(c).strip().lower() for c in df.columns]
    if normalized_columns == ["onset_seconds", "speaker_id"]:
        out = df.copy()
        out.columns = ["onset_seconds", "speaker_id"]
    else:
        out = df.copy()
        out.columns = ["onset_seconds", "speaker_id"]

    out["onset_seconds"] = pd.to_numeric(out["onset_seconds"], errors="coerce")
    out["speaker_id"] = pd.to_numeric(out["speaker_id"], errors="coerce")
    out = out.dropna(subset=["onset_seconds", "speaker_id"]).copy()
    out["speaker_id"] = out["speaker_id"].astype(int)
    out = out.sort_values(["onset_seconds", "speaker_id"], kind="mergesort").reset_index(drop=True)

    if out.empty:
        raise ValueError(f"{path.name} produced an empty input after parsing")
    if out["onset_seconds"].iloc[0] < 0:
        raise ValueError(f"{path.name} contains negative onset_seconds")

    return out


def build_lsh_series(df: pd.DataFrame) -> pd.DataFrame:
    max_second = int(math.floor(df["onset_seconds"].max()))
    seconds = np.arange(0, max_second + 1, dtype=int)

    onset_floor = np.floor(df["onset_seconds"].to_numpy()).astype(int)
    speaker_ids = df["speaker_id"].to_numpy(dtype=int)

    # Handle multiple turn starts within the same second by retaining the last listed onset
    per_second = pd.DataFrame({"second": onset_floor, "speaker_id": speaker_ids}).groupby("second", as_index=False).last()
    known_seconds = per_second["second"].to_numpy(dtype=int)
    known_speakers = per_second["speaker_id"].to_numpy(dtype=int)

    idx = np.searchsorted(known_seconds, seconds, side="right") - 1
    if idx.min() < 0:
        first_speaker = int(df.loc[df["onset_seconds"].idxmin(), "speaker_id"])
        speaker_series = np.full(seconds.shape, first_speaker, dtype=int)
        valid = idx >= 0
        speaker_series[valid] = known_speakers[idx[valid]]
    else:
        speaker_series = known_speakers[idx]

    out = pd.DataFrame({"second": seconds.astype(int), "speaker_id": speaker_series.astype(int)})
    return out


def validate_lsh_series(meeting_id: str, input_df: pd.DataFrame, lsh_df: pd.DataFrame) -> dict:
    expected_max = int(math.floor(input_df["onset_seconds"].max()))
    second_values = lsh_df["second"].to_numpy(dtype=int)
    expected_seconds = np.arange(0, expected_max + 1, dtype=int)

    no_gaps = np.array_equal(second_values, expected_seconds)
    no_null_speaker = bool(lsh_df["speaker_id"].notna().all())
    speaker_match = set(lsh_df["speaker_id"].unique()).issubset(set(input_df["speaker_id"].unique()))
    duration_match = int(lsh_df["second"].max()) == expected_max

    return {
        "meeting_id": meeting_id,
        "duration_seconds": int(expected_max),
        "no_gaps": bool(no_gaps),
        "no_null_speaker_id": bool(no_null_speaker),
        "speaker_id_match": bool(speaker_match),
        "duration_consistent": bool(duration_match),
        "all_checks_pass": bool(no_gaps and no_null_speaker and speaker_match and duration_match),
    }


def summarize_meeting(meeting_id: str, input_df: pd.DataFrame, lsh_df: pd.DataFrame) -> dict:
    duration_seconds = int(lsh_df["second"].max())
    n_turns = int(len(input_df))
    observed_speakers = sorted(int(s) for s in input_df["speaker_id"].unique())
    n_speakers = len(observed_speakers)

    counts = lsh_df["speaker_id"].value_counts().to_dict()
    total_seconds = len(lsh_df)

    row = {
        "meeting_id": meeting_id,
        "duration_seconds": duration_seconds,
        "n_turns": n_turns,
        "n_speakers": n_speakers,
    }

    for position in range(1, 6):
        if position <= len(observed_speakers):
            speaker_id = observed_speakers[position - 1]
            pct = 100.0 * counts.get(speaker_id, 0) / total_seconds
        else:
            pct = 0.0
        row[f"speaker_{position}_pct"] = pct

    return row


def plot_floor_time_distribution(summary_df: pd.DataFrame, output_path: Path) -> None:
    ordered = summary_df.sort_values("duration_seconds").reset_index(drop=True)
    x = np.arange(len(ordered))
    bottom = np.zeros(len(ordered))

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(14, 7))
    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2"]

    for idx, col in enumerate([f"speaker_{i}_pct" for i in range(1, 6)]):
        values = ordered[col].to_numpy(dtype=float)
        ax.bar(x, values, bottom=bottom, label=f"Speaker {idx + 1}", color=colors[idx], width=0.85)
        bottom += values

    ax.set_xlabel("Meeting (sorted by duration)")
    ax.set_ylabel("Floor time (%)")
    ax.set_title("Floor Time Distribution by Meeting")
    ax.set_ylim(0, 100)
    ax.legend(ncol=5, fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ordered["meeting_id"], rotation=90, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_duration_distribution(summary_df: pd.DataFrame, output_path: Path) -> None:
    duration_minutes = summary_df["duration_seconds"] / 60.0
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(duration_minutes, bins=min(12, max(5, len(duration_minutes) // 2)), color="#4C78A8", edgecolor="white")
    ax.set_xlabel("Meeting duration (minutes)")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Startup Meeting Durations")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_example_series(example_df: pd.DataFrame, meeting_id: str, output_path: Path) -> None:
    clipped = example_df[example_df["second"] <= 600].copy()
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.step(clipped["second"] / 60.0, clipped["speaker_id"], where="post", color="#E45756", linewidth=1.5)
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Speaker ID")
    ax.set_title(f"Example LSH Series (First 10 Minutes): {meeting_id}")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def iter_input_files(input_dir: Path) -> Iterable[Path]:
    return sorted(input_dir.glob("*_lsh_input.csv"))


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.figures_dir.mkdir(parents=True, exist_ok=True)

    input_files = list(iter_input_files(args.input_dir))
    if not input_files:
        raise FileNotFoundError(f"No input files matching *_lsh_input.csv found in {args.input_dir}")

    summary_rows = []
    validation_rows = []
    example_meeting_id = None
    example_lsh_df = None

    for input_path in input_files:
        meeting_id = input_path.name.replace("_lsh_input.csv", "")
        output_path = args.output_dir / f"{meeting_id}_lsh.csv"
        input_df = load_input(input_path)
        lsh_df = build_lsh_series(input_df)
        validation = validate_lsh_series(meeting_id, input_df, lsh_df)
        if not validation["all_checks_pass"]:
            raise ValueError(f"Validation failed for {meeting_id}: {validation}")

        if args.force or not output_path.exists():
            lsh_df.to_csv(output_path, index=False)

        summary_rows.append(summarize_meeting(meeting_id, input_df, lsh_df))
        validation_rows.append(validation)

        if example_meeting_id is None:
            example_meeting_id = meeting_id
            example_lsh_df = lsh_df.copy()

    summary_df = pd.DataFrame(summary_rows).sort_values("meeting_id").reset_index(drop=True)
    validation_df = pd.DataFrame(validation_rows).sort_values("meeting_id").reset_index(drop=True)

    summary_df.to_csv(SUMMARY_PATH, index=False)
    validation_df.to_csv(VALIDATION_PATH, index=False)

    plot_floor_time_distribution(summary_df, args.figures_dir / "floor_time_distribution.png")
    plot_duration_distribution(summary_df, args.figures_dir / "duration_distribution.png")
    if example_lsh_df is not None and example_meeting_id is not None:
        plot_example_series(example_lsh_df, example_meeting_id, args.figures_dir / "example_lsh_series.png")

    duration_minutes = summary_df["duration_seconds"] / 60.0
    print(f"Processed {len(summary_df)} meetings")
    print(f"Mean duration (min): {duration_minutes.mean():.2f}")
    print(f"Mean turns: {summary_df['n_turns'].mean():.2f}")
    print(f"Mean speakers: {summary_df['n_speakers'].mean():.2f}")
    print(f"Mean floor share speaker 1 (%): {summary_df['speaker_1_pct'].mean():.2f}")
    print(f"Validation file: {VALIDATION_PATH}")
    print(f"Summary file: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
