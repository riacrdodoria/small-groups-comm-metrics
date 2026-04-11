# 05_llm_classification

This stage classifies each **Step 04 inflection point** with an LLM using the **shared mental model (SMM)** coding schema specified for the project. For every inflection point, the pipeline extracts a transcript segment centered on the detected `peak_second`, formats the local interaction context, sends that context to the model, validates the returned JSON, and writes a reproducible event-level classification table.

| Item | Path |
|---|---|
| Input 1 | `data/processed/inflection_points/inflection_points.csv` |
| Input 2 | `data/anonymized/{meeting_id}/{meeting_id}_transcript.csv` |
| Output | `data/processed/llm_classification/llm_classifications.csv` |
| Checkpoint | `data/processed/llm_classification/llm_classifications_checkpoint.csv` |
| Console summary | `data/processed/llm_classification/step05_console_summary.txt` |

The pipeline keeps the transcript content in its original language during extraction, including Portuguese segments, but requires the model to return all classification fields in **English**. To reduce the risk of losing progress during a long run across 595 events, the script saves an intermediate checkpoint every 50 classifications.

## Context window

The event context window is centered on the detected inflection-point peak.

| Parameter | Value |
|---|---|
| `CONTEXT_BEFORE` | `120` seconds |
| `CONTEXT_AFTER` | `120` seconds |
| Effective segment window | `peak_second ± 120 s` |
| Minimum context size | `3` transcript turns |

Each extracted segment is formatted as timestamped speaker turns such as `[Speaker 2, t=52s]: ...`, preserving event order by `onset_seconds`.

## SMM schema

The model returns one JSON object per inflection point using the project schema below.

| Field | Allowed values | Meaning |
|---|---|---|
| `smm_impact` | `disrupts`, `proposes`, `updates`, `neutral` | Whether the event challenged, introduced, refined, or did not materially affect the team’s shared mental model |
| `smm_dimension` | `task_understanding`, `strategy`, `roles`, `constraints`, `goals`, `none` | Which aspect of the shared mental model was affected |
| `smm_perturbation` | `TRUE` / `FALSE` | `TRUE` when `smm_impact` is `disrupts` or `proposes` |
| `perturbation_type` | `factual_correction`, `role_challenge`, `goal_reframe`, `constraint_revelation`, `generative_tension`, `none` | Type of perturbation when applicable |
| `trigger_content_summary` | One sentence | Short English description of the content that drove the structural change |
| `confidence` | `high`, `medium`, `low` | Confidence in the classification |

The implementation also includes two explicit fallback behaviors required for robust batch processing. First, if the model returns invalid JSON that cannot be salvaged, the event is marked as `parse_error`. Second, if the meeting transcript is missing, the event is marked as `no_transcript`. In the corrected rerun, neither fallback was needed. In addition, the script now enforces a **non-empty `trigger_content_summary`** and supplies a deterministic fallback sentence if the model omits that field.

## Output schema

The final CSV contains one row per Step 04 inflection point.

| Column | Description |
|---|---|
| `meeting_id` | Meeting identifier |
| `peak_second` | Peak second of the detected inflection point |
| `onset_second` | Event onset second from Step 04 |
| `offset_second` | Event offset second from Step 04 |
| `combined_delta` | Step 04 event magnitude summary |
| `smm_impact` | SMM impact label |
| `smm_dimension` | SMM dimension label |
| `smm_perturbation` | Boolean perturbation flag |
| `perturbation_type` | Perturbation subtype |
| `trigger_content_summary` | One-sentence content summary |
| `confidence` | Classification confidence |
| `segment_n_turns` | Number of turns extracted in the transcript segment |
| `segment_duration_seconds` | Nominal transcript window duration |

## Validated rerun results

The corrected rerun completed successfully across the full Step 04 event set.

> === Step 5: LLM Event Classification ===
> Total inflection points processed: 595
> Successful classifications: 595
> Parse errors: 0
> No transcript: 0
> Low confidence: 1 (0.2%)

### `smm_impact` distribution

| Label | Count | Share |
|---|---:|---:|
| `disrupts` | 61 | 10.3% |
| `proposes` | 322 | 54.1% |
| `updates` | 202 | 33.9% |
| `neutral` | 10 | 1.7% |
| `parse_error` | 0 | 0.0% |
| `no_transcript` | 0 | 0.0% |

### `smm_perturbation`

| Flag | Count | Share |
|---|---:|---:|
| `TRUE` | 383 | 64.4% |
| `FALSE` | 212 | 35.6% |

### `perturbation_type` distribution among `TRUE`

| Type | Count | Share |
|---|---:|---:|
| `factual_correction` | 36 | 9.4% |
| `role_challenge` | 6 | 1.6% |
| `goal_reframe` | 12 | 3.1% |
| `constraint_revelation` | 64 | 16.7% |
| `generative_tension` | 265 | 69.2% |

### Confidence distribution

| Level | Count | Share |
|---|---:|---:|
| `high` | 593 | 99.7% |
| `medium` | 1 | 0.2% |
| `low` | 1 | 0.2% |

## Next step

Step 06 will compute **Cohen’s kappa** on a stratified random sample of events to assess agreement between the LLM coding and a human-coded benchmark.
