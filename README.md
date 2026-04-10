# Cognitive Reorganization in Team Meetings: Reproducible Analysis Pipeline

This repository contains a fully scripted and reproducible analysis pipeline for studying **cognitive reorganization in team meetings** from raw transcript data through statistical modeling and cross-context comparison. The project is designed to support a paper submitted to *Small Groups Research* by ensuring that every major transformation, metric, classification decision, and inferential result is generated from code rather than manual processing. The repository is organized so that identifiable source data remain local, anonymized outputs can be shared safely, and every downstream result can be regenerated in a documented sequence.

## Study overview

The repository currently supports two related empirical contexts. **Study 1** focuses on startup team meetings, beginning with raw identifiable transcript files that are anonymized locally before any shareable artifacts are created. In the current project snapshot, **34 startup meetings were processed in the first-pass anonymization run**, while **2 corrupted startup transcripts were excluded from the analytic sample** and one accidental instruction upload was discarded. **Study 2** extends the pipeline to external team communication contexts using the **Gorman et al. (2020)** pre-processed interaction series, including **surgical teams** and **submarine crews**. Together, these studies enable both within-context analysis of cognitive reorganization dynamics and cross-context assessment of whether the same communication mechanisms generalize across team settings.

## Repository structure

```text
small-groups-comm-metrics/
├── README.md
├── .gitignore
├── data/
│   ├── raw/                        # never committed; local only
│   │   ├── startup/                # one CSV per meeting, identifiable
│   │   ├── gorman/                 # Gorman et al. 2020 pre-processed series
│   │   └── entity_list.csv         # researcher-maintained, never committed
│   ├── anonymized/                 # safe to commit after anonymization
│   │   └── startup/
│   ├── processed/                  # outputs of Steps 1–11
│   │   ├── lsh/
│   │   ├── metrics/
│   │   ├── inflection_points/
│   │   └── events/
│   └── human_coding/               # researcher manual annotations
├── prompts/
├── analysis/
│   ├── 00_anonymization/
│   ├── 01_lsh/
│   ├── 02_metrics/
│   ├── 03_convergent_validity/
│   ├── 04_inflection_points/
│   ├── 05_event_classification/
│   ├── 06_interrater_kappa/
│   ├── 07_precision_recall/
│   ├── 08_glmer/
│   ├── 09_trigger_taxonomy/
│   ├── 10_two_mechanism_model/
│   └── 11_cross_context/
└── figures/
```

## How to reproduce

To reproduce the full pipeline, first clone the repository and create a Python environment suitable for the scripts that will be added to each analysis step.

```bash
git clone https://github.com/riacrdodoria/small-groups-comm-metrics.git
cd small-groups-comm-metrics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Next, populate the local-only `data/raw/` directory with the required inputs before running any analysis scripts. Startup meeting transcript CSV files should be placed in `data/raw/startup/`, the Gorman et al. input files should be placed in `data/raw/gorman/`, and the researcher-maintained entity mapping file should remain local at `data/raw/entity_list.csv`.

After the raw files are in place, run the analysis directories in numerical order. The intended workflow is to execute Step 0 first for anonymization and then proceed sequentially through Steps 1 through 11 so that each stage reads standardized outputs from earlier stages and writes new reproducible artifacts to `data/anonymized/`, `data/processed/`, and `figures/`.

```bash
python analysis/00_anonymization/main.py
python analysis/01_lsh/main.py
python analysis/02_metrics/main.py
python analysis/03_convergent_validity/main.py
python analysis/04_inflection_points/main.py
python analysis/05_event_classification/main.py
python analysis/06_interrater_kappa/main.py
python analysis/07_precision_recall/main.py
python analysis/08_glmer/main.py
python analysis/09_trigger_taxonomy/main.py
python analysis/10_two_mechanism_model/main.py
python analysis/11_cross_context/main.py
```

## Analysis steps

| Step | Folder | Primary input | Primary output | Description |
|---|---|---|---|---|
| 00 | `analysis/00_anonymization/` | `data/raw/startup/`, `data/raw/entity_list.csv` | `data/anonymized/startup/` | Removes or replaces identifiable entities so startup transcripts can be analyzed safely. |
| 01 | `analysis/01_lsh/` | `data/anonymized/startup/*_lsh_input.csv` | `data/processed/lsh/`, `figures/01_lsh/` | Builds 1 Hz Last-Speaker-Holds time series, summary tables, validation checks, and diagnostic figures for each startup meeting. |
| 02 | `analysis/02_metrics/` | `data/processed/lsh/` | `data/processed/metrics/` | Derives meeting-level and time-series communication metrics used in downstream analyses. |
| 03 | `analysis/03_convergent_validity/` | `data/processed/metrics/`, `data/human_coding/` | `data/processed/metrics/`, `figures/` | Evaluates whether computed metrics align with related human-coded or theoretically adjacent constructs. |
| 04 | `analysis/04_inflection_points/` | `data/processed/metrics/` | `data/processed/inflection_points/` | Detects candidate points where communication dynamics shift substantially over time. |
| 05 | `analysis/05_event_classification/` | `data/processed/inflection_points/`, `data/anonymized/startup/`, `data/raw/gorman/` | `data/processed/events/` | Labels detected change points as substantively meaningful communication events. |
| 06 | `analysis/06_interrater_kappa/` | `data/human_coding/`, `data/processed/events/` | `data/processed/events/`, `figures/` | Quantifies interrater agreement for manual coding and event annotation decisions. |
| 07 | `analysis/07_precision_recall/` | `data/processed/events/`, `data/human_coding/` | `data/processed/events/`, `figures/` | Assesses event detection performance using precision, recall, and related summary measures. |
| 08 | `analysis/08_glmer/` | `data/processed/metrics/`, `data/processed/events/` | `figures/`, model outputs | Fits generalized linear mixed-effects models for the paper’s main inferential results. |
| 09 | `analysis/09_trigger_taxonomy/` | `data/processed/events/`, `data/human_coding/` | `figures/`, taxonomy outputs | Organizes detected events into a trigger taxonomy grounded in coded evidence. |
| 10 | `analysis/10_two_mechanism_model/` | Outputs from Steps 2, 5, 8, and 9 | `figures/`, model summaries | Integrates findings into a two-mechanism explanatory model of cognitive reorganization. |
| 11 | `analysis/11_cross_context/` | Startup outputs and Gorman-context outputs | `figures/`, comparative summaries | Compares patterns across startup meetings, surgical teams, and submarine crews. |

## Data privacy note

**Raw identifiable data are never committed to the repository.** All files stored in `data/raw/` remain local only. Shareable outputs may be committed only after the anonymization workflow in **Step 0** has been executed and any residual speaker or entity mapping files containing personally identifiable information have been excluded from version control. In the current startup dataset, the files `2025.03.10xPulsoUltraCharge.txt` and `2025.03.02PulsoE-life.txt` are explicitly excluded from the analytic sample because the transcripts are corrupted or dominated by unusable transcription output.

## Current status

Step 0 has now been implemented as a reproducible anonymization pipeline in `analysis/00_anonymization/main.py`, and the corresponding documentation has been added in `analysis/00_anonymization/README.md`. After an initial publication, a manual inspection detected residual personal names in some startup transcripts; the deterministic entity list was expanded, the step was rerun with `--force`, and the committed anonymized outputs were regenerated as the **corrected Step 0 baseline**. The current Step 0 baseline processed 34 startup meetings, excluded 3 uploaded files, and generated anonymized outputs plus a researcher review file for unresolved entities.

Step 1 has now also been completed in `analysis/01_lsh/main.py`. The current LSH baseline generated per-meeting 1 Hz floor-holder time series for all 34 startup meetings, together with `lsh_summary.csv`, `lsh_validation.csv`, and three diagnostic figures in `figures/01_lsh/`. All processed meetings passed the scripted validation checks. Subsequent commits will implement Steps 2–11 in sequence while preserving the rule that each completed step updates both the codebase and the relevant documentation.
