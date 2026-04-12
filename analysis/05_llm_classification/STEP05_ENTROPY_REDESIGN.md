# Step 05 redesign brief: Entropy-UCL classification and GLMER

This note operationalizes the revised **Step 05** specification after the Step 04 redesign. The primary event set is no longer the legacy **595 RMSE-based inflection points**. Instead, Step 05 must consume the **176 Entropy-UCL events** now stored in `data/processed/inflection_points/inflection_points.csv` and treat the legacy RMSE event set only as historical context.

| Item | Path or requirement |
|---|---|
| Primary input | `data/processed/inflection_points/inflection_points.csv` |
| Event count | `176` Entropy-UCL events |
| Meetings in source sample | `34` total meetings |
| Meetings with at least one event | `28` |
| Meetings with zero events | `6` |
| Mandatory carry-through field | `joint_corroborated` |
| Transcript source | `data/anonymized/{meeting_id}/{meeting_id}_transcript.csv` |
| Context window | `peak_second ± 180 s` |

## Required event-level inputs

For each Entropy-UCL event, the classification stage must preserve or extract the following fields before calling the model.

| Field | Role in Step 05 |
|---|---|
| `meeting_id` | Cluster identifier and transcript lookup key |
| `peak_second` | Anchor for transcript extraction |
| `peak_entropy` | Peak structural value at the Entropy excursion |
| `combined_delta` | Event-level magnitude summary from Step 04 |
| `z_delta_entropy` | Standardized pre/post Entropy change |
| `z_delta_pct_det` | Standardized pre/post %DET change |
| `joint_corroborated` | Boolean marker for the strict Entropy + %DET structural subset |
| `temporal_position` | Relative timing within the meeting |

## Classification objective

The coding question is no longer whether an event reflects general SMM perturbation. The new primary outcome is the **type of reorganization when an Entropy-UCL event occurs**. Every event must therefore be classified into one of two top-level categories.

> **Decision 1:** `cognitive_perturbation` versus `functional_reorientation`

The downstream subtype, dimension, and confidence codebook must follow the prior brief unchanged.

| Decision layer | Allowed values |
|---|---|
| Trigger type | `cognitive_perturbation`, `functional_reorientation` |
| CP subtype | `CP_constraint`, `CP_generative`, `CP_divergence`, `CP_invalidation`, `CP_forced` |
| FR subtype | `FR_attention`, `FR_role`, `FR_elaboration`, `FR_procedural`, `FR_social` |
| SMM dimension | `smm_task`, `smm_strategy`, `smm_roles`, `smm_constraints`, `smm_goals`, `smm_none` |
| Confidence | `conf_high`, `conf_medium`, `conf_low` |

## Prompting requirement

The model prompt must explicitly anchor the event to the new structural interpretation.

> "This is a moment where Entropy exceeded its meeting-specific upper control limit — meaning communication was unusually varied and complex at this moment. Your task is to identify what in the transcript content explains this structural departure."

The transcript content should remain in its source language during extraction, but all returned labels and explanatory fields should remain standardized in English.

## Mandatory calibration stop

Before any full run, Step 05 must generate a **20-case calibration sample** and stop for human approval.

| Calibration constraint | Required minimum |
|---|---:|
| Distinct meetings represented | `5` |
| `include` meetings represented | `3` |
| `include_with_caution` meetings represented | `2` |
| `joint_corroborated = True` | `8` |
| `joint_corroborated = False` | `8` |
| Timing coverage | early, middle, and late events all present |

The calibration outputs must be written to the following location.

| Output | Path |
|---|---|
| Calibration sample table | `data/processed/step05_calibration/calibration_sample.csv` |
| Calibration memo | `data/processed/step05_calibration/calibration_report.md` |

After writing those files, the pipeline must **stop and wait for human approval** before classifying the remaining `156` events.

## Full-run outputs after approval

Once the calibration sample is approved, the remaining events should be classified and combined with the calibration cases.

| Output | Path |
|---|---|
| Final classified event table | `data/processed/step05_classification/inflection_points_classified.csv` |
| Classification summary report | `data/processed/step05_classification/classification_summary.md` |
| Prompt log | `data/processed/step05_classification/prompt_log.jsonl` |

## GLMER specification

The intended mixed-effects model should treat the trigger type as a binary outcome.

> `trigger_type ~ joint_corroborated + peak_entropy + combined_delta + temporal_position + trigger_subtype_generative + smm_dimension + confidence + (1 | meeting_id)`

| Modeling element | Specification |
|---|---|
| Outcome | `trigger_type`: `cognitive_perturbation = 1`, `functional_reorientation = 0` |
| Model family | Mixed-effects logistic regression |
| Random effect | `(1 | meeting_id)` |
| Inference | Cluster-robust standard errors by `meeting_id` |
| Reporting | Odds ratios, 95% confidence intervals, and p-values |
| Sensitivity analysis | Refit on the `joint_corroborated = True` subset (`39` events in the current Step 04 output) |

## Required summary contents

The final Step 05 summary must explicitly document the sparsity structure created by the Entropy detector.

| Required section | Content |
|---|---|
| Trigger-type distribution | Counts and percentages overall and by meeting |
| Subtype distribution | Counts and percentages for all ten subtype codes |
| SMM dimensions | Distribution of `smm_dimension` |
| Confidence distribution | Distribution of `conf_high`, `conf_medium`, and `conf_low` |
| Group comparison | Mean `peak_entropy` and `combined_delta` by `trigger_type`, with Mann–Whitney tests |
| Joint corroboration comparison | CP versus FR rates by `joint_corroborated`, with chi-square test |
| Human review queue | All `conf_low` cases listed explicitly |
| Model results | Full GLMER coefficient table |
| Coverage note | Explicit statement that `6` meetings have zero Entropy-UCL events and therefore do not enter the classification dataset |

## Feasibility note from the current event set

A quick check of the redesigned Step 04 output confirms that the requested calibration design is feasible with the current event set.

| Available stratum | Count |
|---|---:|
| Total events | `176` |
| `joint_corroborated = True` | `39` |
| `joint_corroborated = False` | `137` |
| Early events | `72` |
| Middle events | `63` |
| Late events | `41` |
| Events from `include` meetings | `134` |
| Events from `include_with_caution` meetings | `42` |

These counts are sufficient to draw a 20-case calibration sample satisfying the requested joint-corroboration, meeting-quality, and temporal-spread constraints.
