# 04_inflection_points

This directory contains the code and documentation for the **inflection points** stage of the reproducible analysis pipeline.

## Step 4 — Candidate Inflection Points

Input: `data/processed/metrics/*_metrics.csv`  
Output: `data/processed/inflection_points/`, `figures/04_inflection_points/`

### Detection logic

For each meeting, the pipeline smooths the second-by-second Entropy, %DET, and RMSE series with a centered rolling median (`15` s). It then computes a **local shift signal** for each metric as the difference between the mean of the following `30` seconds and the mean of the preceding `30` seconds. These shift signals are robustly standardized within meeting, combined into a composite magnitude score, and filtered so that a second must have at least `2` valid metrics to be eligible.

Candidate inflection points are selected as local maxima of the composite score that exceed an **adaptive threshold** defined as the larger of the meeting-specific `95%` quantile and `median + 2.5 × robust scale`. Nearby peaks are merged with a minimum separation of `60` seconds.

### Results

Meetings processed: `34`  
Total candidate inflection points: `281`  
Mean candidates per meeting: `8.26`  
Median candidates per meeting: `8.00`  
Maximum candidates in a single meeting: `13`

Highest-scoring candidate: `2025.02.24startup_b` at second `158` with composite score `4.819`.

### Files

| File | Purpose |
|---|---|
| `main.py` | Detects candidate inflection points from the dynamic metric series and exports summary tables plus diagnostic figures. |
| `data/processed/inflection_points/meeting_inflection_summary.csv` | One row per meeting with thresholds, valid coverage, and candidate counts. |
| `data/processed/inflection_points/all_inflection_candidates.csv` | Pooled table of candidate seconds, scores, and top contributing metrics across meetings. |
| `data/processed/inflection_points/*_inflection_scores.csv` | Per-second inflection scores and candidate flags for each meeting. |
| `figures/04_inflection_points/*_inflection_points.png` | Meeting-level diagnostic panels showing raw metrics, smoothed metrics, and selected candidate points. |
