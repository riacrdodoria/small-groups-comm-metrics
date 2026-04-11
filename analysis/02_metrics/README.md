# 02_metrics

This directory contains the code and documentation for the **metrics** stage of the reproducible analysis pipeline.

## Step 2 — Dynamic Communication Metrics

Input:  `data/processed/lsh/*_lsh.csv`
Output: `data/processed/metrics/*_metrics.csv`
        `data/processed/metrics/metrics_summary.csv`
        `data/processed/metrics/metrics_correlations.csv`

### Parameters

Entropy:  window = 61s (centered), Shannon H
%DET:     window = 301s (centered), min diagonal = 2
RMSE:     lookback window = 30s, Δn = 20s, ε = 3.0 %DET units

### Results

Meetings processed: 34 (26 include, 8 include_with_caution)
Audit source for Step 2 inventory: `data/processed/quality_audit/startup_meeting_quality_audit_v2.csv` after the targeted Step 0 cleanup for the four previously high-review-flag meetings.
Entropy: mean = 0.910 (SD = 0.154)
%DET:    mean = 97.557 (SD = 1.182)
RMSE:    mean = 0.323 (SD = 0.081), coverage = 99.58%
Correlations (pooled): entropy–pct_det r=-0.470, entropy–rmse r=0.262, pct_det–rmse r=-0.504

### Files

- `main.py` computes second-level dynamic communication metrics for all retained meetings.
- `data/processed/sample_inventory_audit.csv` stores the definitive Step 2 quality labels copied from `data/processed/quality_audit/startup_meeting_quality_audit_v2.csv` after the post-cleanup audit refresh.
- `data/processed/metrics/` stores per-meeting metrics plus the summary and correlation tables.
- `figures/02_metrics/` stores pooled distributions, an example time series panel, between-meeting variability plots, and the metric scatter matrix.
