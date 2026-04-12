# Step 05: LLM event classification

Step 05 classifies each **Entropy-UCL inflection-point event** as either **Cognitive Pivot (CP)** or **Frame Reinforcement (FR)** using an LLM and a fixed transcript window centered on the event peak. This stage is intentionally split into two parts. First, the pipeline runs a constrained **20-case calibration sample** for human inspection. Second, and only after explicit approval, the same method is applied to the remaining events in the approved Step 05 universe.

| Item | Path |
|---|---|
| Primary event input | `data/processed/inflection_points/inflection_points.csv` |
| Transcript input | `data/anonymized/{meeting_id}_transcript.csv` and equivalent anonymized transcript paths already stored under `data/anonymized/` |
| Step 05 redesign brief | `analysis/05_llm_classification/STEP05_ENTROPY_REDESIGN.md` |
| Calibration script | `analysis/05_llm_classification/classify_calibration_sample.py` |
| External full-run handoff | `analysis/05_llm_classification/EXTERNAL_FULL_RUN_HANDOFF.md` |
| Approved calibration sample | `data/processed/step05_calibration/calibration_sample.csv` |
| Calibration output target | `data/processed/step05_calibration/calibration_classifications.csv` |
| Calibration review report | `data/processed/step05_calibration/calibration_report.md` |
| Full-run output folder | `data/processed/step05_classification/` |

The current Step 05 design no longer uses the earlier 595-event workflow documented in older drafts. The approved event universe for this paper is the **176-event Entropy-UCL set**, and the classification target is no longer the broader SMM-impact schema used in earlier exploratory versions. Instead, the approved production workflow uses the more focused **CP-versus-FR codebook** described in the redesign brief.

## Approved redesign

The redesigned calibration sample was approved after the initial sample was rejected for over-concentration within a single meeting and poor temporal balance. The current approved sample satisfies the project constraints and serves as the only valid entry point for Step 05 execution.

| Calibration design criterion | Approved target |
|---|---|
| Calibration sample size | `20` cases |
| Maximum cases per meeting | `2` |
| Distinct meetings represented | `18` |
| Middle or late events | `12` |
| `quality_label = include` | `12` |
| `joint_corroborated = TRUE` | `10` |
| `joint_corroborated = FALSE` | `10` |
| Stop rule | Do not run the remaining `156` events until calibration is reviewed and approved |

Methodological consistency is the main requirement of this stage. Every event must be classified from a transcript segment centered on the event peak, the transcript content must remain in the **source language**, and all model-returned labels, summaries, and justifications must be written in **English**.

## Context window and classification target

| Parameter | Approved value |
|---|---|
| Event universe | `176` Entropy-UCL events |
| Event anchor | `peak_second` |
| Transcript window | `peak_second ± 180 seconds` |
| Primary labels | `CP` = Cognitive Pivot; `FR` = Frame Reinforcement |
| Required carry-through field | `joint_corroborated` |
| Execution order | Calibration first, then human review, then full run |

The transcript window must be extracted deterministically from the anonymized transcript file for the corresponding `meeting_id`. The production script is expected to preserve event-level metadata needed for later summaries and modeling, including timing, corroboration, and event-strength fields.

## Inputs and outputs

The calibration stage and the full run must remain separated for reproducibility and auditability. Calibration artifacts must never be overwritten by the later full-run script.

| Stage | Required inputs | Required outputs |
|---|---|---|
| Calibration | `inflection_points.csv`, anonymized transcripts, `calibration_sample.csv`, `classify_calibration_sample.py` | `calibration_classifications.csv`, `calibration_report.md` |
| Full run | `inflection_points.csv`, anonymized transcripts, approved Step 05 method | `step05_classification/inflection_points_classified.csv`, `step05_classification/classification_summary.md`, `step05_classification/prompt_log.jsonl` |

The calibration output file is intentionally separate from the eventual full-run output table. This makes it possible to inspect classification behavior on the approved sample before spending resources on the remaining 156 events.

## Current execution status

At the moment, the **repository contains the approved calibration sample, the calibration script, and the external handoff materials**, but the actual Step 05 model run remains blocked in this environment. The Manus proxy endpoint currently returns route failures, so the production LLM classification cannot be completed here until the endpoint is restored or the same workflow is executed in another environment.

| Operational item | Current status |
|---|---|
| Approved calibration sample | Ready |
| Calibration script | Ready |
| Full-run handoff instructions | Ready |
| Local Step 05 execution in Manus | Blocked by unavailable proxy route |
| Recommended workaround | Run the same workflow externally using `EXTERNAL_FULL_RUN_HANDOFF.md` |

The file `EXTERNAL_FULL_RUN_HANDOFF.md` explains how to reproduce the Step 05 full run outside Manus without redesigning the method. If you use Claude Code or another external coding agent, that document is the authoritative handoff for creating and running the full 176-event classifier while preserving the approved Step 05 logic.

## Important note on current calibration artifacts

The files under `data/processed/step05_calibration/` are versioned so that the approved sample design and current execution state are fully documented. However, if a local run failed because the model endpoint was unavailable or unauthorized, those outputs should be treated as **execution artifacts rather than substantive classification evidence**. The correct next action is to rerun the approved 20-case calibration with a working model endpoint, inspect the resulting report, and only then decide whether to launch the remaining 156 events.

## Next step

The next valid milestone is to execute the approved 20-case calibration with a working LLM endpoint, generate a clean calibration report, and pause for review. Only after that review should the project create the final full-run outputs for the complete 176-event Step 05 dataset.
