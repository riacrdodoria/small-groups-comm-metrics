# Step 05 Full-Run Classification Summary

**Total events classified:** 176  
**Classification date:** 2026-04-12  
**Model:** claude-sonnet-4-6 (direct in-context classification)  

## 1. Overall Distribution

| Category | n | % |
|---|---|---|
| cognitive_perturbation | 51 | 29.0% |
| functional_reorientation | 125 | 71.0% |
| **Total** | **176** | **100%** |

## 2. CP Subtypes

| Subtype | n | % of CP |
|---|---|---|
| CP_generative | 38 | 74.5% |
| CP_constraint | 11 | 21.6% |
| CP_divergence | 1 | 2.0% |
| CP_invalidation | 1 | 2.0% |
| **Total CP** | **51** | **100%** |

## 3. FR Subtypes

| Subtype | n | % of FR |
|---|---|---|
| FR_elaboration | 73 | 58.4% |
| FR_procedural | 43 | 34.4% |
| FR_attention | 7 | 5.6% |
| FR_role | 1 | 0.8% |
| FR_social | 1 | 0.8% |
| **Total FR** | **125** | **100%** |

## 4. SMM Dimensions

| Dimension | n | % |
|---|---|---|
| smm_strategy | 149 | 84.7% |
| smm_task | 20 | 11.4% |
| smm_goals | 3 | 1.7% |
| smm_roles | 2 | 1.1% |
| smm_constraints | 1 | 0.6% |
| smm_none | 1 | 0.6% |

## 5. Confidence Levels

| Level | n | % |
|---|---|---|
| conf_medium | 165 | 93.8% |
| conf_high | 11 | 6.2% |

## 6. Joint Corroboration

| Group | joint_corroborated=True | total | rate |
|---|---|---|---|
| All events | 39 | 176 | 22.2% |
| CP events | 13 | 51 | 25.5% |
| FR events | 26 | 125 | 20.8% |

## 7. CP Rate by Joint Corroboration

| Corroboration | CP | total | CP rate |
|---|---|---|---|
| joint_corroborated=True | 13 | 39 | 33.3% |
| joint_corroborated=False | 38 | 137 | 27.7% |

## 8. Per-Meeting Summary

| meeting_id | total | CP | FR | CP rate |
|---|---|---|---|---|
| 2024.10.14startup_a | 6 | 1 | 5 | 16.7% |
| 2024.10.25startup_a | 7 | 4 | 3 | 57.1% |
| 2024.10.28startup_b | 8 | 2 | 6 | 25.0% |
| 2024.11.04startup_a | 6 | 3 | 3 | 50.0% |
| 2024.11.04startup_b | 5 | 0 | 5 | 0.0% |
| 2024.11.11startup_a | 5 | 4 | 1 | 80.0% |
| 2024.11.11startup_b | 6 | 3 | 3 | 50.0% |
| 2024.11.18startup_a | 7 | 3 | 4 | 42.9% |
| 2024.11.18startup_b | 9 | 3 | 6 | 33.3% |
| 2024.12.09startup_a | 7 | 3 | 4 | 42.9% |
| 2024.12.16startup_b | 5 | 1 | 4 | 20.0% |
| 2024.12.23startup_a | 6 | 0 | 6 | 0.0% |
| 2024.12.23startup_b | 5 | 1 | 4 | 20.0% |
| 2025.01.13startup_a | 10 | 2 | 8 | 20.0% |
| 2025.01.13startup_b | 8 | 2 | 6 | 25.0% |
| 2025.02.24startup_a | 3 | 0 | 3 | 0.0% |
| 2025.02.24startup_b | 10 | 1 | 9 | 10.0% |
| 2025.03.02startup_a | 8 | 3 | 5 | 37.5% |
| 2025.03.17startup_a | 4 | 0 | 4 | 0.0% |
| 2025.03.17startup_b | 5 | 1 | 4 | 20.0% |
| 2025.03.24startup_b | 4 | 2 | 2 | 50.0% |
| 2025.03.25startup_a | 7 | 2 | 5 | 28.6% |
| 2025.03.31startup_a | 5 | 1 | 4 | 20.0% |
| 2025.03.31startup_b | 9 | 3 | 6 | 33.3% |
| 2025.04.07startup_a | 4 | 1 | 3 | 25.0% |
| 2025.04.07startup_b | 7 | 3 | 4 | 42.9% |
| 2025.04.14startup_a | 9 | 2 | 7 | 22.2% |
| 2025.04.14startup_b | 1 | 0 | 1 | 0.0% |

## 9. Low-Confidence Events (conf_low queue)

No events classified as conf_low.

## 10. Calibration Events

20 calibration events (cal_01–cal_20) were classified in the calibration phase and merged by (meeting_id, peak_second) matching.

Calibration results file: `data/processed/step05_calibration/calibration_classifications.csv`
