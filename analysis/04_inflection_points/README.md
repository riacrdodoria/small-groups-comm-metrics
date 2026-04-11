# 04_inflection_points

This directory contains the corrected **Step 04 — Inflection Point Identification** stage of the reproducible analysis pipeline. The current implementation replaces the earlier composite-score prototype with a meeting-specific **upper control limit (UCL)** rule applied directly to the second-by-second **RMSE** series.

## Analytical objective

The purpose of Step 04 is to identify candidate temporal segments in which the dynamic communication system shows unusually large disruption in recurrence structure. In the corrected workflow, those candidate segments are operationalized as intervals where a meeting's observed RMSE rises above a meeting-specific statistical control threshold. The resulting events are then summarized with contextual changes in **Entropy** and **%DET** so that downstream stages can prioritize interpretable perturbations rather than raw RMSE exceedances alone.

## Inputs and outputs

The pipeline reads all per-second metric files from `data/processed/metrics/` and writes the corrected Step 04 products to `data/processed/inflection_points/` and `figures/04_inflection_points/`.

| Path | Description |
|---|---|
| `main.py` | Corrected Step 04 pipeline implementing the per-meeting UCL rule on RMSE and the downstream summary calculations. |
| `data/processed/inflection_points/inflection_points.csv` | Event-level table containing all retained inflection points and their contextual metric deltas. |
| `data/processed/inflection_points/inflection_points_summary.csv` | Meeting-level summary table containing event counts, average event characteristics, UCL, quality label, and meeting duration. |
| `figures/04_inflection_points/rmse_ucl_distribution.png` | Pooled RMSE distributions split by `include` versus `include_with_caution`, with the mean UCL marked in each panel. |
| `figures/04_inflection_points/inflection_points_per_meeting.png` | Meeting-level bar chart showing the retained number of inflection points, colored by quality label. |
| `figures/04_inflection_points/temporal_position_distribution.png` | Histogram of retained inflection-point temporal positions across all meetings. |
| `figures/04_inflection_points/combined_delta_distribution.png` | Histogram of `combined_delta` across retained inflection points, with the pooled mean marked. |
| `figures/04_inflection_points/example_meeting_panel.png` | Three-panel example figure for the meeting with the median number of retained inflection points. |

## Corrected detection algorithm

For each meeting, the pipeline estimates a meeting-specific **upper control limit** from the valid RMSE observations outside the edge window.

> Let **M** be the meeting mean of RMSE, **SD** the meeting standard deviation of RMSE, and **t** the one-tailed critical value from the *t* distribution with significance level `alpha = 0.05` and `df = n - 1`, where **n** is the number of valid RMSE seconds in that meeting. The upper control limit is computed as **UCL = M + t × SD**.

Every second satisfying `RMSE > UCL` is initially marked as part of a candidate exceedance interval. Consecutive candidate seconds are merged into one episode. Within each merged episode, the pipeline retains the second with the largest RMSE as the provisional peak. If two provisional peaks are separated by fewer than **60 seconds**, the lower-RMSE peak is discarded; this comparison is repeated through rank-based filtering until no retained pair violates the minimum separation rule.

Each retained peak is then contextualized with two 30-second windows, one immediately before the peak and one immediately after it. For **Entropy** and **%DET**, the pipeline computes pre-window means, post-window means, and absolute changes. These changes are standardized using the meeting-level standard deviation of the corresponding metric, yielding `z_delta_entropy` and `z_delta_pct_det`. The summary field `combined_delta` is the average of those two standardized deltas, but it is set to missing whenever either metric lacks at least **10 valid non-edge seconds** in the pre or post window.

## Event-level schema

The corrected event table follows the schema requested for downstream compatibility.

| Column | Description |
|---|---|
| `meeting_id` | Meeting identifier derived from the metrics filename. |
| `onset_second` | First second in the contiguous RMSE-above-UCL episode. |
| `offset_second` | Last second in the contiguous RMSE-above-UCL episode. |
| `peak_second` | Retained second within the episode with the highest RMSE. |
| `peak_rmse` | RMSE value at `peak_second`. |
| `alpha_level` | Fixed one-tailed significance level used to define the UCL (`0.05`). |
| `ucl` | Meeting-specific upper control limit used for detection. |
| `temporal_position` | Relative timing of the peak within the meeting, computed as `peak_second / meeting_duration_seconds`. |
| `combined_delta` | Mean of `z_delta_entropy` and `z_delta_pct_det` when both window-coverage criteria are satisfied; otherwise missing. |
| `pre_entropy` / `post_entropy` | Mean entropy in the 30 seconds immediately before and after the peak. |
| `delta_entropy` | Absolute difference between `post_entropy` and `pre_entropy`. |
| `z_delta_entropy` | `delta_entropy` standardized by the meeting-level entropy standard deviation. |
| `pre_pct_det` / `post_pct_det` | Mean %DET in the 30 seconds immediately before and after the peak. |
| `delta_pct_det` | Absolute difference between `post_pct_det` and `pre_pct_det`. |
| `z_delta_pct_det` | `delta_pct_det` standardized by the meeting-level %DET standard deviation. |

## Meeting-level schema

| Column | Description |
|---|---|
| `meeting_id` | Meeting identifier. |
| `quality_label` | Meeting audit label imported from `sample_inventory_audit.csv`. |
| `n_inflection_points` | Number of retained peaks after episode merging and 60-second de-duplication. |
| `mean_peak_rmse` | Mean of `peak_rmse` across retained peaks in the meeting. |
| `mean_combined_delta` | Mean `combined_delta` across retained peaks in the meeting. |
| `mean_temporal_position` | Mean relative timing of retained peaks within the meeting. |
| `ucl` | Meeting-specific UCL. |
| `meeting_duration_seconds` | Meeting duration represented in the metrics file. |

## Regenerated results

The corrected rerun processed **34 meetings** and detected **595 retained inflection points**. The mean number of retained inflection points per meeting was **17.50** with **SD = 1.88** and a range from **12** to **22**. Across all retained events, the mean peak RMSE was **0.882**, the mean meeting-specific UCL was **0.663**, and the mean `combined_delta` was **0.717** with **SD = 0.288**. No meeting had zero retained inflection points.

The average retained count was **17.35** among meetings labeled `include` and **18.00** among meetings labeled `include_with_caution`. The example figure produced in this rerun corresponds to **`2024.10.14startup_b`**, which was selected because its retained count was closest to the sample median.

## Interpretation notes

These Step 04 outputs are intended to identify **candidate perturbation episodes** rather than definitive regime changes. The UCL threshold isolates statistically unusual RMSE elevations within each meeting, while `combined_delta` adds a descriptive summary of whether neighboring entropy and determinism values also shift around the detected peak. Downstream steps should therefore treat Step 04 as a structured candidate-generation stage for further classification, validation, or qualitative interpretation.
