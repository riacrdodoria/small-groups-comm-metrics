# Step 05 Quality Check Report

**Date:** 2026-04-12  
**Input:** `data/processed/step05_classification/inflection_points_classified.csv`  

## 1. Summary

| | n | % |
|---|---|---|
| Total events | 176 | 100% |
| **Flagged (low quality)** | **155** | **88.1%** |
| Pass (not flagged) | 21 | 11.9% |

## 2. Criteria Breakdown

| Criterion | Events flagged |
|---|---|
| `justification` < 15 words | 154 |
| `content_summary` < 8 words | 39 |
| Generic phrase in `content_summary` | 21 |
*(events can trigger multiple criteria)*

## 3. Flagged by trigger_type

| trigger_type | flagged | total | flag rate |
|---|---|---|---|
| cognitive_perturbation | 39 | 51 | 76.5% |
| functional_reorientation | 116 | 125 | 92.8% |

## 4. Flagged by trigger_subtype

| trigger_subtype | flagged |
|---|---|
| FR_elaboration | 67 |
| FR_procedural | 41 |
| CP_generative | 30 |
| CP_constraint | 8 |
| FR_attention | 6 |
| FR_role | 1 |
| CP_invalidation | 1 |
| FR_social | 1 |

## 5. Flagged by joint_corroborated

| joint_corroborated | flagged | total | flag rate |
|---|---|---|---|
| True | 29 | 39 | 74.4% |
| False | 126 | 137 | 92.0% |

## 6. Note on Calibration Events

Calibration events (classifier=calibration) are NOT flagged — they have full justifications from the calibration run.
All 155 flagged events have classifier=full_run.

## 7. Next Step

Awaiting human approval to proceed with Passo 2 (API reclassification of 155 flagged events).
