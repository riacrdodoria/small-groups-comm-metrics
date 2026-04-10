# Step 1 — LSH (Last-Speaker-Holds)

This step converts each anonymized startup meeting from turn onsets into a **1 Hz integer time series** using the Last-Speaker-Holds rule. The goal is to create a consistent second-by-second representation of who holds the conversational floor at each moment, which serves as the foundation for all downstream communication dynamics metrics.

| Item | Location |
| --- | --- |
| Input | `data/anonymized/startup/*_lsh_input.csv` |
| Per-meeting output | `data/processed/lsh/*_lsh.csv` |
| Summary output | `data/processed/lsh/lsh_summary.csv` |
| Validation output | `data/processed/lsh/lsh_validation.csv` |
| Figures | `figures/01_lsh/` |
| Main script | `analysis/01_lsh/main.py` |

## Results

The step was executed on the full current startup sample after the permanent exclusion of the two unusable meetings documented in Step 0.

| Metric | Value |
| --- | --- |
| Meetings processed | 34 |
| Mean duration | 91.69 min (SD = 6.47) |
| Mean turns per meeting | 514.35 (SD = 141.88) |
| Mean speakers per meeting | 4.12 (SD = 0.59) |
| Mean floor share, Speaker 1 | 36.19% |

All meetings passed the scripted validation checks. The generated validation table confirms that each output time series contains no gaps, no null speaker values, only speaker IDs observed in the source file, and a duration consistent with the last observed turn onset.

## Method note

The LSH rule assigns each second to the **most recent speaker** whose turn onset occurred at or before that second. No silence code is used. The last speaker therefore holds the floor continuously until another speaker begins. The series starts at `t = 0` and ends at `floor(max(onset_seconds))` for the meeting.

In practice, the script reads each `{meeting_id}_lsh_input.csv` file with columns `[onset_seconds, speaker_id]`, sorts the turn onsets, and builds a complete integer sequence of seconds. For each second, it carries forward the most recent speaker assignment. The output for each meeting is written as `{meeting_id}_lsh.csv` with integer columns `[second, speaker_id]`.

| Validation check | Description |
| --- | --- |
| No gaps | Every integer second from 0 through the final second is present |
| No null values | `speaker_id` is assigned at every second |
| Speaker ID match | Output `speaker_id` values are a subset of the input speaker IDs |
| Duration consistency | Final second equals `floor(max(onset_seconds))` |

## Generated files

The step writes one processed LSH file per meeting, together with one summary table, one validation table, and three diagnostic figures.

| File | Purpose |
| --- | --- |
| `data/processed/lsh/*_lsh.csv` | Per-meeting 1 Hz LSH time series |
| `data/processed/lsh/lsh_summary.csv` | Meeting-level summary statistics |
| `data/processed/lsh/lsh_validation.csv` | Validation results for each meeting |
| `figures/01_lsh/floor_time_distribution.png` | Stacked bar chart of floor share by meeting |
| `figures/01_lsh/duration_distribution.png` | Histogram of meeting duration in minutes |
| `figures/01_lsh/example_lsh_series.png` | Example first-10-minute LSH trajectory |

## Reproduction

From the repository root, run:

```bash
python3 analysis/01_lsh/main.py --force
```

The `--force` flag regenerates all per-meeting outputs even if prior files already exist. This step does **not** read from `data/raw/` and does **not** modify `data/anonymized/`.
