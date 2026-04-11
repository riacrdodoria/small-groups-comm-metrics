# 03_convergent_validity

This directory contains the code and documentation for the **convergent validity** stage of the reproducible analysis pipeline.

## Step 3 — Convergent Validity

Input: `data/raw/gorman/*` (Gorman standard-method 1 Hz series in Excel format)  
Output: `data/processed/convergent_validity/`

### Method note

LSH-equivalent series are created by forward-filling silence codes (`speaker_id = 0`) with the most recent active speaker. If a series starts with silence, the initial gap is backward-filled from the first active speaker. This isolates the single methodological difference between the LSH approach and the standard Gorman coding method while preserving the original second-by-second timeline.

The parser now preserves both numeric `0` values and string-coded silence labels such as `"0"`, `"silence"`, and related variants. Workbooks that do not contain a usable speaker-by-second transcript schema are explicitly skipped and logged in the inventory instead of being coerced into artificial time series.

### Verified anomaly resolution

The apparent perfect overlap previously observed for `J10T3Output-Cz_Seq` and `J5S2_Team6_ScenarioB` was caused by **two different data issues**.

| File | Verified raw-data finding | Resolution in the reproducible pipeline |
|---|---|---|
| `J10T3Output-Cz_Seq.xls` | The raw `Speaker` column contains the literal string `"0"`, so silence is present in the source workbook. | The parser was corrected to treat string-coded `"0"` as silence. After the fix, the series are no longer identical and the meeting-level correlations dropped to Entropy `r = 0.776`, `%DET r = 0.909`, and `RMSE r = 0.548`. |
| `J5S2_Team6_ScenarioB.xlsx` | The raw workbook is not a speaker-by-second transcript. Its columns are stage labels, free-text scenario instructions, and instructor identifiers, with no usable second column or speaker-code column. | The file is now marked as `skipped` with `context = unsupported_schema` in `gorman_series_inventory.csv`, and it is excluded from the corrected v2 temporal outputs. |

### Results

Surgical teams (experienced + student, N = 8 teams):  
Entropy: `r = 0.888` (95% CI `[0.885, 0.891]`), `p = 0`  
%DET: `r = 0.754` (95% CI `[0.748, 0.760]`), `p = 0`  
RMSE: `r = 0.529` (95% CI `[0.518, 0.539]`), `p = 0`  
Mean silence: `25.95%`

Submarine crews (experienced + less experienced, N = 7 crews):  
Entropy: `r = 0.932` (95% CI `[0.931, 0.933]`), `p = 0`  
%DET: `r = 0.827` (95% CI `[0.824, 0.830]`), `p = 0`  
RMSE: `r = 0.521` (95% CI `[0.513, 0.528]`), `p = 0`  
Mean silence: `36.31%`

### Temporal-comparison outputs

The corrected per-meeting plots and summary are written to the following v2 locations:

| Output | Path |
|---|---|
| Per-meeting figures | `figures/03_convergent_validity/temporal_meetings_v2/` |
| Per-meeting summary table | `data/processed/convergent_validity/temporal_comparison_v2/meeting_temporal_correlation_summary.csv` |
| Per-meeting summary report | `data/processed/convergent_validity/temporal_comparison_v2/meeting_temporal_correlation_summary.md` |

### Files

| File | Purpose |
|---|---|
| `main.py` | Loads the available Gorman Excel files, extracts valid standard 1 Hz speaker series, creates the LSH-equivalent forward-filled version, computes Entropy, %DET, and RMSE for both versions, and exports the comparison outputs. |
| `meeting_temporal_comparison.py` | Builds per-meeting temporal plots and a corrected v2 summary from the regenerated Step 03 outputs. |
| `data/processed/convergent_validity/convergent_validity_results.csv` | Stores per-team metric correlations between the standard and LSH-equivalent series. |
| `data/processed/convergent_validity/metrics_standard_all.csv` | Stores pooled second-level metrics for the standard-method series. |
| `data/processed/convergent_validity/metrics_lsh_all.csv` | Stores pooled second-level metrics for the LSH-equivalent series. |
| `data/processed/convergent_validity/domain_summary.csv` | Stores pooled domain-level correlations used in this README. |
| `data/processed/convergent_validity/gorman_series_inventory.csv` | Records which Gorman workbooks were processed versus skipped, including the reason for any exclusion. |
| `figures/03_convergent_validity/` | Stores the scatter plots, silence distribution figure, and temporal comparison directories. |
