# External handoff for Step 05 full run

If you decide to run the **Step 05 full classification outside Manus**, you already have almost everything needed inside the repository. The external runner does **not** need to redesign the method. It only needs to reproduce the approved entropy-based Step 05 workflow, keep the calibration outputs for reference, and then classify the full **176-event Entropy-UCL dataset** with the same coding schema and transcript-window logic.

| Item | Requirement |
|---|---|
| Primary event file | `data/processed/inflection_points/inflection_points.csv` |
| Transcript source | `data/anonymized/{meeting_id}/{meeting_id}_transcript.csv` |
| Step 05 redesign brief | `analysis/05_llm_classification/STEP05_ENTROPY_REDESIGN.md` |
| Calibration script | `analysis/05_llm_classification/classify_calibration_sample.py` |
| Approved calibration sample | `data/processed/step05_calibration/calibration_sample.csv` |
| Calibration artifacts and sample documentation | `data/processed/step05_calibration/calibration_sample.csv`, `data/processed/step05_calibration/calibration_classifications.csv`, `data/processed/step05_calibration/calibration_report.md` |
| Step 05 stage overview | `analysis/05_llm_classification/README.md` |

The most important point is methodological consistency. The outside runner should **preserve exactly the same Step 05 logic** that was approved here: the event universe is the **176 Entropy-UCL events**, each event is anchored on `peak_second`, the transcript window is **`peak_second ± 180 seconds`**, the transcript remains in the original language, and the returned labels and justifications are standardized in **English**.

The current repository also includes calibration-stage output files produced while the local model route was unavailable. Those files are useful as **execution-state documentation** and for checking schemas, but they are **not a substitute for a successful calibration run**. If they show endpoint or authorization failures, the outside runner should treat them as technical artifacts and rerun the approved 20-case calibration with a working model before attempting the full 176-event pass.

| Core design decision | Value to preserve |
|---|---|
| Event universe | 176 Entropy-UCL events |
| Meeting coverage in source | 34 meetings total, 28 with at least one event |
| Classification target | `cognitive_perturbation` vs. `functional_reorientation` |
| Transcript window | `peak_second ± 180 s` |
| Mandatory carry-through field | `joint_corroborated` |
| Output language | English labels and English justifications |
| Stop rule | Keep calibration separate; do not overwrite it |

The external runner should use the existing calibration script as the baseline implementation, because it already encodes the correct codebook, JSON schema, transcript normalization, and report structure. In practice, the easiest path is to **duplicate and adapt** that script into a full-run script rather than writing a new classifier from scratch.

| Recommended files to hand to the outside AI | Why they matter |
|---|---|
| `analysis/05_llm_classification/STEP05_ENTROPY_REDESIGN.md` | Defines the approved Step 05 method and final deliverables |
| `analysis/05_llm_classification/classify_calibration_sample.py` | Contains the actual prompt, schema, parsing logic, and report logic |
| `data/processed/step05_calibration/calibration_sample.csv` | Shows the approved calibration schema and field names |
| `data/processed/step05_calibration/calibration_report.md` | Shows the expected review structure, even if a failed local attempt must later be replaced |
| `data/processed/inflection_points/inflection_points.csv` | Provides the full 176-event input set |
| `data/anonymized/` | Provides the transcript material needed for context extraction |

The outside AI should be told to create a new script, for example `analysis/05_llm_classification/classify_full_entropy_run.py`, that follows the calibration script closely but operates on **all 176 events** instead of only the approved 20-case sample. It should also avoid overwriting prior files, because preserving the calibration history is useful for auditability and later comparison.

| What the full-run script should do | Expected behavior |
|---|---|
| Load events | Read `data/processed/inflection_points/inflection_points.csv` |
| Load transcripts | Resolve `data/anonymized/{meeting_id}/{meeting_id}_transcript.csv` or equivalent existing path |
| Extract context | Build transcript windows from `peak_second - 180` to `peak_second + 180` |
| Prompt the model | Use the CP-vs-FR codebook and the same structured JSON schema |
| Validate outputs | Enforce allowed labels and deterministic fallbacks for malformed responses |
| Log prompts | Save all prompts and raw responses to JSONL |
| Write event table | Save one row per event with all input and output fields |
| Write summary | Save a Markdown report with distributions and quality checks |

The external runner does **not** need to guess the prompt. The prompt is already present in `classify_calibration_sample.py`. That script defines the system instruction, the subtype rules, the SMM dimension rules, the confidence rules, the exact JSON response keys, and the transcript formatting. Those elements should be reused nearly verbatim so that the full run remains comparable to the approved calibration stage.

Before launching the full run, the outside environment should first rerun the approved 20-case calibration sample and confirm that the resulting report contains substantive classifications rather than endpoint failures. That review checkpoint is mandatory because the project design explicitly requires a human decision between the 20-case calibration and the remaining 156 events.

| Exact output fields the model should return per event | Notes |
|---|---|
| `trigger_type` | `cognitive_perturbation` or `functional_reorientation` |
| `trigger_subtype` | One of the 10 approved CP/FR subtype labels |
| `smm_dimension` | `smm_task`, `smm_strategy`, `smm_roles`, `smm_constraints`, `smm_goals`, or `smm_none` |
| `confidence` | `conf_high`, `conf_medium`, or `conf_low` |
| `content_summary` | One English sentence of 8–30 words |
| `justification` | One to three English sentences |

In addition to the model-returned fields, the external runner should preserve the event metadata already carried by the calibration script. This is important because the downstream summary and GLMER stage depend on these variables being present in the final classified table.

| Event-level columns to preserve in the final CSV | Reason |
|---|---|
| `meeting_id` | Random-effect cluster and transcript lookup key |
| `peak_second` | Event anchor |
| `onset_second`, `offset_second` | Event boundaries from Step 04 |
| `temporal_position`, `timing_bin` | Temporal analysis and coverage checks |
| `joint_corroborated` | Required subgroup comparison and sensitivity analysis |
| `peak_entropy`, `combined_delta` | Required descriptive and model covariates |
| `z_delta_entropy`, `z_delta_pct_det` | Preserved event diagnostics |
| `peak_pct_det`, `peak_rmse` | Optional descriptive diagnostics retained by script |
| `meeting_duration_seconds` | Meeting-level contextual variable |
| `window_start_second`, `window_end_second` | Auditability of transcript extraction |
| `segment_n_turns` | Reliability and low-context flagging |

The cleanest external workflow is to run a short smoke test first, then a full classification pass, then a report-generation pass. This reduces the risk of discovering an API or parsing problem after many expensive calls.

| Recommended execution sequence | Purpose |
|---|---|
| 1. API smoke test | Confirm that the chosen external model endpoint is reachable and authenticated |
| 2. Dry run on 3–5 events | Confirm JSON formatting, field names, and prompt behavior |
| 3. Full 176-event run | Generate the complete classification table |
| 4. Summary report generation | Produce distributions and review queues |
| 5. Manual review of `conf_low` cases | Check ambiguous windows before GLMER |

If you use **Claude Code** or another outside coding agent, the most effective prompt is one that forbids method drift. The agent should be told explicitly not to redesign the codebook, not to shorten the transcript window, not to translate transcript content before classification, and not to change the allowed label sets.

| Suggested instructions for the outside AI | Required constraint |
|---|---|
| Preserve Step 05 method | Do not redesign the schema or logic |
| Preserve context extraction | Use `peak_second ± 180 s` |
| Preserve transcript language | Keep transcript text in original language |
| Preserve output language | Return English labels and English explanations |
| Preserve calibration history | Write new full-run outputs to a new folder |
| Preserve logging | Save prompt log with raw responses |

You can hand the outside AI the following prompt almost as-is:

```text
You are extending an existing repository workflow, not redesigning the method. Read these files first: analysis/05_llm_classification/STEP05_ENTROPY_REDESIGN.md and analysis/05_llm_classification/classify_calibration_sample.py. Create a new script called analysis/05_llm_classification/classify_full_entropy_run.py that applies the same CP-versus-FR codebook and transcript-window extraction logic to all 176 events in data/processed/inflection_points/inflection_points.csv. Use transcript windows centered on peak_second ± 180 seconds. Keep transcript content in the source language, but require all returned labels, summaries, and justifications in English. Preserve event metadata fields including meeting_id, peak_second, onset_second, offset_second, temporal_position, timing_bin, joint_corroborated, peak_entropy, combined_delta, z_delta_entropy, z_delta_pct_det, peak_pct_det, peak_rmse, meeting_duration_seconds, window_start_second, window_end_second, and segment_n_turns. Reuse the existing JSON schema, validation logic, deterministic fallbacks, and report style from the calibration script. Write outputs to data/processed/step05_classification/inflection_points_classified.csv, data/processed/step05_classification/classification_summary.md, and data/processed/step05_classification/prompt_log.jsonl. Do not overwrite calibration files. Also generate a review section listing all conf_low cases explicitly.
```

The final deliverables expected from the external full run are already defined in the redesign brief and should be treated as mandatory. If the outside runner changes these file names, it will make the downstream workflow harder to compare with the approved plan.

| Mandatory full-run outputs | Path |
|---|---|
| Final classified event table | `data/processed/step05_classification/inflection_points_classified.csv` |
| Classification summary report | `data/processed/step05_classification/classification_summary.md` |
| Prompt log | `data/processed/step05_classification/prompt_log.jsonl` |

The summary report should do more than list counts. It should explicitly show the overall CP-versus-FR split, subtype counts, SMM dimension counts, confidence distribution, trigger type by `joint_corroborated`, trigger type by meeting, and a clear queue of all `conf_low` cases for manual review. It should also preserve the coverage note that **6 meetings have zero Entropy-UCL events** and therefore do not enter the Step 05 classified dataset.

| What to review after the external run finishes | Why it matters |
|---|---|
| CP vs FR distribution | Detect obvious collapse to one class |
| Subtype spread | Detect prompt drift or subtype overuse |
| Confidence distribution | Detect fragile classification quality |
| `joint_corroborated` comparison | Needed for the planned sensitivity analysis |
| `conf_low` queue | Manual quality control before modeling |
| Missing transcripts or parse failures | Detect technical rather than substantive problems |

If the outside AI is going to write code automatically, I recommend that you ask it to first produce the script, then run a tiny smoke test on a handful of events, then wait for your confirmation before launching the full 176-event call sequence. That gives you one more checkpoint and reduces the chance of wasting tokens or money on a broken prompt or parser.

| Minimal practical package you should send | Enough to execute the job? |
|---|---|
| Repository or zipped `analysis/05_llm_classification/` folder | Yes, for method and scripts |
| `data/processed/inflection_points/inflection_points.csv` | Yes, mandatory |
| `data/anonymized/` transcript files | Yes, mandatory |
| `data/processed/step05_calibration/` outputs | Strongly recommended |
| Working API key or model access in the outside environment | Yes, mandatory |

In short, if the Manus proxy does not recover, you are still in good shape to run this elsewhere. What you need is **the redesign brief, the calibration script, the full inflection-point CSV, the transcript folder, and a working external model endpoint**. With those pieces, another AI can reproduce the Step 05 method without inventing a new workflow.
