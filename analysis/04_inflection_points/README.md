# 04_inflection_points

This directory contains **Step 04 — Inflection Point Identification** for the reproducible analysis pipeline. The current implementation preserves the meeting-specific **RMSE-based upper control limit (UCL)** detector used to define the retained event set, while extending the event diagnostics to include meeting-specific control limits for **Entropy** and **%DET (determinism)** as well as an expanded three-metric `combined_delta_v2`.

## Analytical objective

The purpose of Step 04 is to identify candidate temporal segments in which the dynamic communication system shows unusually large disruption in recurrence structure. In the current workflow, retained events are still defined by intervals in which a meeting's observed **RMSE** exceeds a meeting-specific statistical control threshold. The extension implemented in this version adds two complementary layers of evidence. First, each retained RMSE peak is annotated with the corresponding **Entropy** and **%DET** values at the same second together with their meeting-specific control limits. Second, each retained peak receives a three-metric contextual summary that incorporates pre/post changes in **RMSE**, **Entropy**, and **%DET**.

This design allows the pipeline to remain backward compatible with the existing Step 05 classification stage while directly addressing the concern that RMSE alone may be a noisy primary detector. The additional fields make it possible to evaluate whether an RMSE-defined peak is corroborated by contemporaneous departures in Entropy or %DET and whether the surrounding communication dynamics shift across all three metrics rather than only the original two contextual measures.

## Inputs and outputs

The pipeline reads all per-second metric files from `data/processed/metrics/` and writes the Step 04 products to `data/processed/inflection_points/` and `figures/04_inflection_points/`.

| Path | Description |
|---|---|
| `main.py` | Step 04 pipeline implementing RMSE-based UCL detection plus Entropy/%DET control-limit diagnostics and expanded combined-delta summaries. |
| `data/processed/inflection_points/inflection_points.csv` | Event-level table containing all retained inflection points, pre/post metric deltas, and auxiliary Entropy/%DET control-limit fields. |
| `data/processed/inflection_points/inflection_points_summary.csv` | Meeting-level summary table containing event counts, average event characteristics, per-metric UCL values, corroboration counts, quality label, and meeting duration. |
| `data/processed/inflection_points/inflection_point_metadata.csv` | Meeting-level metadata table containing valid-second counts, means, standard deviations, and upper/lower control limits for RMSE, Entropy, and %DET. |
| `figures/04_inflection_points/metric_ucl_distributions.png` | Six-panel figure showing pooled per-second distributions for RMSE, Entropy, and %DET split by `include` versus `include_with_caution`, with the mean UCL overlaid in each panel. |
| `figures/04_inflection_points/inflection_points_per_meeting.png` | Meeting-level bar chart showing the retained number of inflection points, colored by quality label. |
| `figures/04_inflection_points/temporal_position_distribution.png` | Histogram of retained inflection-point temporal positions across all meetings. |
| `figures/04_inflection_points/combined_delta_distribution.png` | Two-panel histogram comparing the original `combined_delta` with the expanded `combined_delta_v2`. |
| `figures/04_inflection_points/auxiliary_ucl_corroboration.png` | Meeting-level comparison of the proportion of retained RMSE peaks that fall outside the auxiliary Entropy and %DET control limits. |
| `figures/04_inflection_points/example_meeting_panel.png` | Three-panel example figure for the meeting with the median number of retained inflection points, showing RMSE, Entropy, and %DET with their control limits and retained peaks. |

## Detection and diagnostic algorithm

For each meeting, the pipeline estimates meeting-specific control statistics from all valid non-edge seconds. RMSE remains the **primary detector**.

> Let **M** be the meeting mean of a metric, **SD** its meeting standard deviation, and **t** the one-tailed critical value from the *t* distribution with significance level `alpha = 0.05` and `df = n - 1`, where **n** is the number of valid seconds for that metric in the meeting. The upper control limit is computed as **UCL = M + t × SD** and the lower control limit as **LCL = M − t × SD**.

Every second satisfying `RMSE > RMSE_UCL` is initially marked as part of a candidate exceedance interval. Consecutive candidate seconds are merged into one episode. Within each merged episode, the pipeline retains the second with the largest RMSE as the provisional peak. If two provisional peaks are separated by fewer than **60 seconds**, the lower-RMSE peak is discarded; this comparison is repeated through rank-based filtering until no retained pair violates the minimum separation rule.

Each retained peak is then contextualized with two 30-second windows, one immediately before the peak and one immediately after it. For **Entropy**, **%DET**, and **RMSE**, the pipeline computes pre-window means, post-window means, and absolute changes. These changes are standardized by the meeting-level standard deviation of the corresponding metric, yielding `z_delta_entropy`, `z_delta_pct_det`, and `z_delta_rmse`.

The output now contains two complementary combined-delta summaries.

| Field | Definition |
|---|---|
| `combined_delta` | Mean of `z_delta_entropy` and `z_delta_pct_det`, retained for backward compatibility with the earlier Step 04 design. |
| `combined_delta_v2` | Mean of the available standardized pre/post deltas across `z_delta_rmse`, `z_delta_entropy`, and `z_delta_pct_det`, provided that each contributing metric has at least **10 valid non-edge seconds** in both the pre and post windows. |

In addition to window-based deltas, the event table records whether the Entropy and %DET values observed exactly at `peak_second` exceed the metric-specific UCL or fall below the corresponding LCL. The field `auxiliary_ucl_corroboration` is set to `1` whenever either Entropy or %DET falls outside its meeting-specific control limits at the retained RMSE peak.

## Event-level schema

The event table preserves the original RMSE detector fields and adds the auxiliary control-limit diagnostics.

| Column | Description |
|---|---|
| `meeting_id` | Meeting identifier derived from the metrics filename. |
| `onset_second` | First second in the contiguous RMSE-above-UCL episode. |
| `offset_second` | Last second in the contiguous RMSE-above-UCL episode. |
| `peak_second` | Retained second within the episode with the highest RMSE. |
| `peak_rmse` | RMSE value at `peak_second`. |
| `alpha_level` | Fixed one-tailed significance level used to define the control limits (`0.05`). |
| `ucl` | Meeting-specific RMSE upper control limit used for event detection. |
| `temporal_position` | Relative timing of the peak within the meeting, computed as `peak_second / meeting_duration_seconds`. |
| `combined_delta` | Mean of `z_delta_entropy` and `z_delta_pct_det` when the required window coverage is available. |
| `combined_delta_v2` | Expanded mean of standardized RMSE, Entropy, and %DET deltas. |
| `pre_entropy` / `post_entropy` | Mean entropy in the 30 seconds immediately before and after the peak. |
| `delta_entropy` | Absolute difference between `post_entropy` and `pre_entropy`. |
| `z_delta_entropy` | `delta_entropy` standardized by the meeting-level entropy standard deviation. |
| `pre_pct_det` / `post_pct_det` | Mean %DET in the 30 seconds immediately before and after the peak. |
| `delta_pct_det` | Absolute difference between `post_pct_det` and `pre_pct_det`. |
| `z_delta_pct_det` | `delta_pct_det` standardized by the meeting-level %DET standard deviation. |
| `pre_rmse` / `post_rmse` | Mean RMSE in the 30 seconds immediately before and after the peak. |
| `delta_rmse` | Absolute difference between `post_rmse` and `pre_rmse`. |
| `z_delta_rmse` | `delta_rmse` standardized by the meeting-level RMSE standard deviation. |
| `peak_entropy` | Entropy value at the retained RMSE peak second. |
| `entropy_ucl` / `entropy_lcl` | Meeting-specific upper and lower control limits for Entropy. |
| `entropy_exceeds_ucl` / `entropy_below_lcl` / `entropy_outside_limits` | Indicators showing whether Entropy at `peak_second` is above the UCL, below the LCL, or outside either control bound. |
| `entropy_excess_over_ucl` / `entropy_excess_z` | Upper-tail Entropy exceedance over the UCL in raw units and standardized units. |
| `peak_pct_det` | %DET value at the retained RMSE peak second. |
| `pct_det_ucl` / `pct_det_lcl` | Meeting-specific upper and lower control limits for %DET. |
| `pct_det_exceeds_ucl` / `pct_det_below_lcl` / `pct_det_outside_limits` | Indicators showing whether %DET at `peak_second` is above the UCL, below the LCL, or outside either control bound. |
| `pct_det_excess_over_ucl` / `pct_det_excess_z` | Upper-tail %DET exceedance over the UCL in raw units and standardized units. |
| `rmse_excess_over_ucl` / `rmse_excess_z` | RMSE exceedance over the meeting-specific UCL in raw units and standardized units. |
| `auxiliary_ucl_corroboration` | Binary indicator set to `1` when Entropy or %DET falls outside its meeting-specific control limits at the retained RMSE peak. |

## Meeting-level schema

| Column | Description |
|---|---|
| `meeting_id` | Meeting identifier. |
| `quality_label` | Meeting audit label imported from `sample_inventory_audit.csv`. |
| `n_inflection_points` | Number of retained peaks after episode merging and 60-second de-duplication. |
| `mean_peak_rmse` | Mean of `peak_rmse` across retained peaks in the meeting. |
| `mean_peak_entropy` | Mean Entropy value at retained peaks in the meeting. |
| `mean_peak_pct_det` | Mean %DET value at retained peaks in the meeting. |
| `mean_combined_delta` | Mean `combined_delta` across retained peaks in the meeting. |
| `mean_combined_delta_v2` | Mean `combined_delta_v2` across retained peaks in the meeting. |
| `mean_temporal_position` | Mean relative timing of retained peaks within the meeting. |
| `rmse_ucl` | Meeting-specific RMSE upper control limit. |
| `entropy_ucl` | Meeting-specific Entropy upper control limit. |
| `pct_det_ucl` | Meeting-specific %DET upper control limit. |
| `n_entropy_peak_exceeds_ucl` | Count of retained RMSE peaks whose Entropy value exceeds the meeting-specific Entropy UCL. |
| `n_entropy_peak_outside_limits` | Count of retained RMSE peaks whose Entropy value falls outside the meeting-specific Entropy control limits. |
| `n_pct_det_peak_exceeds_ucl` | Count of retained RMSE peaks whose %DET value exceeds the meeting-specific %DET UCL. |
| `n_pct_det_peak_outside_limits` | Count of retained RMSE peaks whose %DET value falls outside the meeting-specific %DET control limits. |
| `n_auxiliary_ucl_corroborated` | Count of retained RMSE peaks corroborated by Entropy or %DET falling outside their meeting-specific control limits. |
| `meeting_duration_seconds` | Meeting duration represented in the metrics file. |

## Regenerated results

The current rerun processed **34 meetings** and retained **595 inflection points**, exactly matching the existing RMSE-defined event set used by downstream steps. The mean number of retained inflection points per meeting was **17.50** with **SD = 1.88** and a range from **12** to **22**. Across all retained events, the mean peak RMSE was **0.882**, the mean meeting-specific RMSE UCL was **0.663**, and the mean `combined_delta` was **0.717** with **SD = 0.288**.

The expanded `combined_delta_v2`, which incorporates standardized RMSE, Entropy, and %DET pre/post changes, was available for **571** of the **595** retained events and had a pooled mean of **0.630** with **SD = 0.238**. The original two-metric `combined_delta` was also available for **571** events, with the same missingness pattern caused by insufficient valid seconds near some meeting edges.

The auxiliary control-limit diagnostics show that **57** retained RMSE peaks had Entropy values outside their meeting-specific control limits and **72** had %DET values outside theirs. In total, **119** of the **595** retained RMSE peaks (**20.0%**) were corroborated by at least one auxiliary control-limit departure at the same second. By contrast, only **21** entropy peaks and **0** %DET peaks were above their respective **upper** control limits alone, confirming that lower-tail departures are important for interpreting these bounded or smoother metrics.

The average retained count was **17.35** among meetings labeled `include` and **18.00** among meetings labeled `include_with_caution`. The example figure produced in this rerun corresponds to **`2024.10.14startup_b`**, which was selected because its retained count was closest to the sample median.

## Interpretation notes

These Step 04 outputs are intended to identify **candidate perturbation episodes** rather than definitive regime changes. The RMSE UCL threshold remains the operational detector used to define the candidate event set, which preserves compatibility with the completed Step 05 classification output. The new Entropy and %DET control-limit fields should be interpreted as **corroborative diagnostics**: they indicate whether a retained RMSE peak coincides with a statistically unusual value in the smoother and theoretically more direct communication metrics.

The expanded `combined_delta_v2` adds a second complementary perspective. Rather than focusing only on the instantaneous metric values at the retained peak, it summarizes whether the surrounding 30-second context changed across all three metrics. Together, the control-limit flags and the new combined-delta measure allow later steps to distinguish between RMSE peaks that are broadly corroborated by communication-system reorganization and peaks that appear more isolated to the RMSE series.
