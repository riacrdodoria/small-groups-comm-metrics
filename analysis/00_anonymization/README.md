# Step 0 — Anonymization

This step removes personally identifiable and organizationally identifiable information from the startup meeting transcripts before any shareable artifacts are used in the downstream pipeline. The implementation is designed so that all identifiable source files remain local in `data/raw/`, while the anonymized outputs in `data/anonymized/startup/` can be committed safely after review.

## Purpose

The anonymization stage standardizes the startup transcript inputs into two downstream-ready formats. First, it creates an **anonymized time series** for the communication-structure analyses used in Steps 1–4 and 10. Second, it creates a **redacted transcript** for the event interpretation tasks used in Steps 5 and 9. In addition, it writes local-only mapping files that preserve the original speaker and entity correspondences for auditability without exposing them in the repository.

## Inputs

| Input | Path | Description |
|---|---|---|
| Startup transcript files | `data/raw/startup/` | Raw identifiable transcript files supplied by the researcher. |
| Researcher entity list | `data/raw/entity_list.csv` | Local-only deterministic replacement list for known people, organizations, startups, clients, and locations. |

## Outputs

| Output | Path pattern | Description |
|---|---|---|
| Anonymized time series | `data/anonymized/startup/{meeting_id}_lsh_input.csv` | Contains `onset_seconds` and anonymized integer `speaker_id` only. |
| Redacted transcript | `data/anonymized/startup/{meeting_id}_transcript.csv` | Contains `onset_seconds`, anonymized integer `speaker_id`, and redacted `text`. |
| Speaker map | `data/anonymized/startup/{meeting_id}_speaker_map.csv` | Local-only mapping from original speaker labels to anonymous integer IDs. Excluded from Git. |
| Entity map | `data/anonymized/startup/{meeting_id}_entity_map.csv` | Local-only audit trail of entity replacements applied in each meeting. Excluded from Git. |
| Review file | `data/anonymized/startup/review_flagged.csv` | Consolidated unresolved named entities requiring researcher review before a final zero-unresolved release. |
| Exclusion summary | `data/anonymized/startup/exclusions.csv` | Records raw files removed from the analytic startup sample. |

## Current implementation

The script in `main.py` performs the following operations in sequence.

1. It screens all files in `data/raw/startup/` and excludes known unusable uploads.
2. It parses transcript lines into a structured turn-level table using onset time, speaker label, and spoken text.
3. It replaces original speaker labels with stable anonymous integer IDs within each meeting.
4. It applies deterministic text replacement from `data/raw/entity_list.csv`.
5. It applies named-entity detection as a fallback to flag or redact additional people, organizations, and locations.
6. It writes the anonymized outputs and local-only mapping files.
7. It aggregates unresolved entities into `review_flagged.csv` for iterative researcher review.

## Excluded startup files

Three uploaded files are currently excluded from the startup analytic sample.

| File | Status | Reason |
|---|---|---|
| `2025.03.10xPulsoUltraCharge.txt` | Excluded | Corrupted transcript with unstable transcription language and insufficient usable meeting structure. |
| `2025.03.02PulsoE-life.txt` | Excluded | Transcript dominated by nonsensical transcription output and therefore unusable for analysis. |
| `pasted_content.txt` | Excluded | Instruction file accidentally uploaded alongside the raw transcripts; not a meeting transcript. |

These exclusions should remain documented in the repository so the startup sample definition is transparent.

## Execution

Run the anonymization step from the repository root.

```bash
python3.11 analysis/00_anonymization/main.py --force
```

The `--force` flag rewrites existing anonymized outputs for a clean rerun after updates to the entity list or anonymization logic.

## First reproducible run summary

The current scripted run processed the startup raw files supplied in this project snapshot and produced the following first-pass summary.

| Metric | Value |
|---|---:|
| Meetings processed | 34 |
| Files excluded | 3 |
| Remaining unresolved entities after first-pass redaction | 3366 |
| Deterministic or fallback person replacements | 323 |
| Deterministic or fallback partner replacements | 1097 |
| Deterministic or fallback client replacements | 27 |
| Deterministic or fallback location replacements | 504 |
| Startup replacements | 22 |

This means the step is already reproducible and generates shareable anonymized artifacts, but the researcher should continue expanding `data/raw/entity_list.csv` and rerun the script until `review_flagged.csv` is reduced to zero or an explicitly accepted review threshold. The current repository state therefore represents a documented **first-pass anonymization baseline** rather than the final locked anonymization dictionary.

## Notes for downstream steps

Steps 1–4 and 10 should use only the `_lsh_input.csv` outputs. Steps 5 and 9 should use the `_transcript.csv` outputs. No downstream step should read from `data/raw/startup/` directly.
