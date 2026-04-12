#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover
    raise SystemExit("The openai package is required. Install it with: sudo pip3 install openai") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CSV = PROJECT_ROOT / "data/processed/step05_calibration/calibration_sample.csv"
INFLECTION_POINTS_CSV = PROJECT_ROOT / "data/processed/inflection_points/inflection_points.csv"
TRANSCRIPT_DIR = PROJECT_ROOT / "data/anonymized"
OUT_DIR = PROJECT_ROOT / "data/processed/step05_calibration"
OUT_CSV = OUT_DIR / "calibration_classifications.csv"
OUT_REPORT = OUT_DIR / "calibration_report.md"
OUT_PROMPT_LOG = OUT_DIR / "prompt_log.jsonl"

MODEL = os.environ.get("STEP05_MODEL", "gpt-4.1-mini")
OPENAI_BASE_URL = "https://api.openai.com/v1"
TEMPERATURE = 0
MAX_RETRIES = 3
SLEEP_BETWEEN_CALLS = 1
CONTEXT_BEFORE = 180
CONTEXT_AFTER = 180

TRIGGER_TYPES = {"cognitive_perturbation", "functional_reorientation"}
CP_SUBTYPES = {
    "CP_constraint",
    "CP_generative",
    "CP_divergence",
    "CP_invalidation",
    "CP_forced",
}
FR_SUBTYPES = {
    "FR_attention",
    "FR_role",
    "FR_elaboration",
    "FR_procedural",
    "FR_social",
}
SMM_DIMENSIONS = {
    "smm_task",
    "smm_strategy",
    "smm_roles",
    "smm_constraints",
    "smm_goals",
    "smm_none",
}
CONFIDENCE_LEVELS = {"conf_high", "conf_medium", "conf_low"}

SYSTEM_PROMPT = """You are coding a transcript window from a team meeting study on cognitive reorganization. The event was detected because Shannon Entropy exceeded the meeting-specific upper control limit, meaning communication became unusually varied and complex at this moment. Your task is to identify whether the transcript content is better explained as cognitive perturbation or functional reorientation.

Definitions:
- cognitive_perturbation (CP): the interaction disrupts, challenges, invalidates, or forces revision of the team’s current understanding, assumptions, constraints, priorities, or interpretation of the situation.
- functional_reorientation (FR): the interaction redirects coordination, attention, roles, procedure, elaboration, or social alignment without clearly disrupting the underlying shared frame.

Subtype rules:
- If trigger_type is cognitive_perturbation, trigger_subtype must be one of:
  - CP_constraint: a new or clarified limitation changes what is feasible.
  - CP_generative: a new possibility or idea expands the conceptual space without direct opposition.
  - CP_divergence: competing interpretations, disagreements, or alternative frames are actively contrasted.
  - CP_invalidation: an existing assumption, claim, or plan is explicitly contradicted or shown to be wrong.
  - CP_forced: an external requirement or decision compels reframing.
- If trigger_type is functional_reorientation, trigger_subtype must be one of:
  - FR_attention: the team redirects focus to a topic, issue, or information stream.
  - FR_role: the team reallocates responsibility, authority, or ownership.
  - FR_elaboration: the team develops, clarifies, or details an existing line of action.
  - FR_procedural: the team changes process, sequencing, or next-step coordination.
  - FR_social: the team repairs alignment, motivation, or interpersonal coordination.

SMM dimension rules:
- smm_task: the nature of the task, problem, or deliverable.
- smm_strategy: plans, tactics, sequencing, or approaches.
- smm_roles: responsibility, ownership, expertise, or authority.
- smm_constraints: time, resources, external dependencies, or restrictions.
- smm_goals: targets, priorities, criteria, or intended outcomes.
- smm_none: no clear shared-mental-model dimension is affected.

Confidence rules:
- conf_high: the evidence is clear and the classification is unambiguous.
- conf_medium: the classification is plausible but some ambiguity remains.
- conf_low: the window is too fragmentary or ambiguous for a reliable decision.

Return exactly one JSON object with these keys:
- calibration_case_id
- meeting_id
- peak_second
- trigger_type
- trigger_subtype
- smm_dimension
- confidence
- content_summary
- justification

Formatting rules:
- All returned labels and explanatory text must be in English.
- content_summary must be one sentence of 8-30 words describing what happens in the window.
- justification must be 1-3 English sentences explaining why the case is CP or FR and why the subtype fits.
- Return only valid JSON, with no markdown fences or extra commentary."""


@dataclass
class EventPayload:
    calibration_case_id: str
    meeting_id: str
    quality_label: str
    peak_second: int
    onset_second: int | None
    offset_second: int | None
    temporal_position: float
    timing_bin: str
    joint_corroborated: bool
    peak_entropy: float | None
    combined_delta: float | None
    z_delta_entropy: float | None
    z_delta_pct_det: float | None
    peak_pct_det: float | None
    peak_rmse: float | None
    meeting_duration_seconds: float | None
    window_start_second: int
    window_end_second: int
    segment_text: str
    segment_n_turns: int


def coerce_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None



def coerce_int(value: Any) -> int | None:
    try:
        if pd.isna(value):
            return None
        return int(round(float(value)))
    except Exception:
        return None



def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()



def extract_json_candidate(text: str) -> str:
    stripped = strip_code_fences(text)
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        return match.group(0)
    return stripped



def find_transcript_path(meeting_id: str) -> Path | None:
    direct = TRANSCRIPT_DIR / meeting_id / f"{meeting_id}_transcript.csv"
    startup = TRANSCRIPT_DIR / "startup" / f"{meeting_id}_transcript.csv"
    if direct.exists():
        return direct
    if startup.exists():
        return startup
    matches = sorted(TRANSCRIPT_DIR.rglob(f"{meeting_id}_transcript.csv"))
    return matches[0] if matches else None



def load_transcript(transcript_path: Path) -> pd.DataFrame:
    transcript = pd.read_csv(transcript_path)
    normalized = {c.lower().strip(): c for c in transcript.columns}

    onset_col = None
    for candidate in ["onset_seconds", "onset_second", "start_seconds", "start_time_seconds"]:
        if candidate in normalized:
            onset_col = normalized[candidate]
            break
    if onset_col is None:
        onset_col = transcript.columns[0]

    speaker_col = None
    for candidate in ["speaker_id", "speaker", "speaker_label", "participant", "role"]:
        if candidate in normalized:
            speaker_col = normalized[candidate]
            break
    if speaker_col is None:
        speaker_col = transcript.columns[1]

    text_col = None
    for candidate in ["text", "utterance", "transcript", "content"]:
        if candidate in normalized:
            text_col = normalized[candidate]
            break
    if text_col is None:
        text_col = transcript.columns[2]

    clean = transcript[[onset_col, speaker_col, text_col]].copy()
    clean.columns = ["onset_seconds", "speaker_id", "text"]
    clean["onset_seconds"] = pd.to_numeric(clean["onset_seconds"], errors="coerce")
    clean["speaker_id"] = clean["speaker_id"].fillna("Unknown").astype(str).str.strip()
    clean["text"] = clean["text"].fillna("").astype(str).str.strip()
    clean = clean.dropna(subset=["onset_seconds"])
    clean = clean[clean["text"] != ""]
    clean["onset_seconds"] = clean["onset_seconds"].round().astype(int)
    clean = clean.sort_values("onset_seconds").reset_index(drop=True)
    return clean



def load_sample() -> pd.DataFrame:
    sample = pd.read_csv(SAMPLE_CSV)
    inflections = pd.read_csv(INFLECTION_POINTS_CSV)
    merge_columns = [
        "meeting_id",
        "peak_second",
        "onset_second",
        "offset_second",
    ]
    inflections = inflections[merge_columns].drop_duplicates(subset=["meeting_id", "peak_second"])
    merged = sample.merge(inflections, on=["meeting_id", "peak_second"], how="left", validate="one_to_one")
    merged["joint_corroborated"] = merged["joint_corroborated"].fillna(False).astype(bool)
    return merged.sort_values("calibration_case_id").reset_index(drop=True)



def build_payload(row: pd.Series, transcript: pd.DataFrame | None) -> EventPayload:
    peak_second = int(row["peak_second"])
    window_start = max(0, peak_second - CONTEXT_BEFORE)
    window_end = peak_second + CONTEXT_AFTER

    if transcript is None:
        segment = pd.DataFrame(columns=["onset_seconds", "speaker_id", "text"])
    else:
        segment = transcript[
            transcript["onset_seconds"].between(window_start, window_end, inclusive="both")
        ].copy()
        segment = segment.sort_values("onset_seconds")

    lines = [
        f"[Speaker {speaker}, t={int(onset)}s]: {text}"
        for onset, speaker, text in segment[["onset_seconds", "speaker_id", "text"]].itertuples(index=False, name=None)
    ]

    return EventPayload(
        calibration_case_id=str(row["calibration_case_id"]),
        meeting_id=str(row["meeting_id"]),
        quality_label=str(row["quality_label"]),
        peak_second=peak_second,
        onset_second=coerce_int(row.get("onset_second")),
        offset_second=coerce_int(row.get("offset_second")),
        temporal_position=float(row["temporal_position"]),
        timing_bin=str(row["timing_bin"]),
        joint_corroborated=bool(row["joint_corroborated"]),
        peak_entropy=coerce_float(row.get("peak_entropy")),
        combined_delta=coerce_float(row.get("combined_delta")),
        z_delta_entropy=coerce_float(row.get("z_delta_entropy")),
        z_delta_pct_det=coerce_float(row.get("z_delta_pct_det")),
        peak_pct_det=coerce_float(row.get("peak_pct_det")),
        peak_rmse=coerce_float(row.get("peak_rmse")),
        meeting_duration_seconds=coerce_float(row.get("meeting_duration_seconds")),
        window_start_second=window_start,
        window_end_second=window_end,
        segment_text="\n".join(lines),
        segment_n_turns=int(len(segment)),
    )



def build_user_prompt(payload: EventPayload) -> str:
    return (
        f"Calibration case ID: {payload.calibration_case_id}\n"
        f"Meeting ID: {payload.meeting_id}\n"
        f"Meeting quality label: {payload.quality_label}\n"
        f"Peak second: {payload.peak_second}\n"
        f"Inflection onset_second: {payload.onset_second}\n"
        f"Inflection offset_second: {payload.offset_second}\n"
        f"Temporal position: {payload.temporal_position:.3f} ({payload.timing_bin})\n"
        f"Joint corroborated: {payload.joint_corroborated}\n"
        f"Peak entropy: {payload.peak_entropy}\n"
        f"Combined delta: {payload.combined_delta}\n"
        f"Z delta entropy: {payload.z_delta_entropy}\n"
        f"Z delta pct_det: {payload.z_delta_pct_det}\n"
        f"Peak pct_det: {payload.peak_pct_det}\n"
        f"Peak rmse: {payload.peak_rmse}\n"
        f"Context window: {payload.window_start_second} to {payload.window_end_second} seconds (peak ±180s)\n"
        f"Transcript turns in window: {payload.segment_n_turns}\n\n"
        "Return one JSON object with this exact schema:\n"
        "{\n"
        f'  "calibration_case_id": "{payload.calibration_case_id}",\n'
        f'  "meeting_id": "{payload.meeting_id}",\n'
        f'  "peak_second": {payload.peak_second},\n'
        '  "trigger_type": "cognitive_perturbation | functional_reorientation",\n'
        '  "trigger_subtype": "CP_constraint | CP_generative | CP_divergence | CP_invalidation | CP_forced | FR_attention | FR_role | FR_elaboration | FR_procedural | FR_social",\n'
        '  "smm_dimension": "smm_task | smm_strategy | smm_roles | smm_constraints | smm_goals | smm_none",\n'
        '  "confidence": "conf_high | conf_medium | conf_low",\n'
        '  "content_summary": "One English sentence of 8-30 words",\n'
        '  "justification": "One to three English sentences explaining the trigger type and subtype"\n'
        "}\n\n"
        "Transcript window:\n"
        f"{payload.segment_text if payload.segment_text else '[No transcript turns in selected window]'}"
    )



def default_subtype(trigger_type: str) -> str:
    return "CP_constraint" if trigger_type == "cognitive_perturbation" else "FR_attention"



def fallback_summary(payload: EventPayload) -> str:
    if not payload.segment_text.strip():
        return "No transcript content was available in the selected event window."
    first_line = payload.segment_text.splitlines()[0]
    first_line = re.sub(r"^\[Speaker .*?\]:\s*", "", first_line).strip()
    if len(first_line) > 120:
        first_line = first_line[:117].rstrip() + "..."
    if not first_line:
        return "The window contained transcript material, but no concise summary was returned."
    return f"The segment centers on: {first_line}"



def sanitize_response(raw: dict[str, Any], payload: EventPayload) -> dict[str, Any]:
    trigger_type = str(raw.get("trigger_type", "functional_reorientation")).strip().lower()
    if trigger_type not in TRIGGER_TYPES:
        trigger_type = "functional_reorientation"

    trigger_subtype = str(raw.get("trigger_subtype", default_subtype(trigger_type))).strip()
    if trigger_type == "cognitive_perturbation":
        if trigger_subtype not in CP_SUBTYPES:
            trigger_subtype = default_subtype(trigger_type)
    else:
        if trigger_subtype not in FR_SUBTYPES:
            trigger_subtype = default_subtype(trigger_type)

    smm_dimension = str(raw.get("smm_dimension", "smm_none")).strip().lower()
    if smm_dimension not in SMM_DIMENSIONS:
        smm_dimension = "smm_none"

    confidence = str(raw.get("confidence", "conf_medium")).strip().lower()
    if confidence not in CONFIDENCE_LEVELS:
        confidence = "conf_medium"
    if payload.segment_n_turns < 3:
        confidence = "conf_low"

    content_summary = str(raw.get("content_summary", "")).strip()
    if not content_summary:
        content_summary = fallback_summary(payload)

    justification = str(raw.get("justification", "")).strip()
    if not justification:
        justification = (
            "The transcript window did not yield a fully structured model justification, so this case should be reviewed manually."
        )

    return {
        "calibration_case_id": payload.calibration_case_id,
        "meeting_id": payload.meeting_id,
        "quality_label": payload.quality_label,
        "peak_second": payload.peak_second,
        "onset_second": payload.onset_second,
        "offset_second": payload.offset_second,
        "temporal_position": payload.temporal_position,
        "timing_bin": payload.timing_bin,
        "joint_corroborated": payload.joint_corroborated,
        "peak_entropy": payload.peak_entropy,
        "combined_delta": payload.combined_delta,
        "z_delta_entropy": payload.z_delta_entropy,
        "z_delta_pct_det": payload.z_delta_pct_det,
        "peak_pct_det": payload.peak_pct_det,
        "peak_rmse": payload.peak_rmse,
        "meeting_duration_seconds": payload.meeting_duration_seconds,
        "window_start_second": payload.window_start_second,
        "window_end_second": payload.window_end_second,
        "segment_n_turns": payload.segment_n_turns,
        "trigger_type": trigger_type,
        "trigger_subtype": trigger_subtype,
        "smm_dimension": smm_dimension,
        "confidence": confidence,
        "content_summary": content_summary,
        "justification": justification,
    }



def classify_case(client: OpenAI, payload: EventPayload) -> tuple[dict[str, Any], dict[str, Any]]:
    user_prompt = build_user_prompt(payload)
    last_error = None
    raw_text = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw_text = response.choices[0].message.content or ""
            parsed = json.loads(extract_json_candidate(raw_text))
            if not isinstance(parsed, dict):
                raise ValueError("Model response JSON is not an object")
            return sanitize_response(parsed, payload), {
                "calibration_case_id": payload.calibration_case_id,
                "meeting_id": payload.meeting_id,
                "peak_second": payload.peak_second,
                "prompt": user_prompt,
                "raw_response": raw_text,
                "status": "ok",
            }
        except Exception as exc:  # pragma: no cover
            last_error = str(exc)
            time.sleep(min(attempt, 3))

    fallback = {
        "calibration_case_id": payload.calibration_case_id,
        "meeting_id": payload.meeting_id,
        "quality_label": payload.quality_label,
        "peak_second": payload.peak_second,
        "onset_second": payload.onset_second,
        "offset_second": payload.offset_second,
        "temporal_position": payload.temporal_position,
        "timing_bin": payload.timing_bin,
        "joint_corroborated": payload.joint_corroborated,
        "peak_entropy": payload.peak_entropy,
        "combined_delta": payload.combined_delta,
        "z_delta_entropy": payload.z_delta_entropy,
        "z_delta_pct_det": payload.z_delta_pct_det,
        "peak_pct_det": payload.peak_pct_det,
        "peak_rmse": payload.peak_rmse,
        "meeting_duration_seconds": payload.meeting_duration_seconds,
        "window_start_second": payload.window_start_second,
        "window_end_second": payload.window_end_second,
        "segment_n_turns": payload.segment_n_turns,
        "trigger_type": "functional_reorientation",
        "trigger_subtype": "FR_attention",
        "smm_dimension": "smm_none",
        "confidence": "conf_low",
        "content_summary": fallback_summary(payload),
        "justification": f"Model parsing failed during the calibration run: {last_error}",
    }
    return fallback, {
        "calibration_case_id": payload.calibration_case_id,
        "meeting_id": payload.meeting_id,
        "peak_second": payload.peak_second,
        "prompt": user_prompt,
        "raw_response": raw_text,
        "status": f"error: {last_error}",
    }



def save_prompt_log(records: list[dict[str, Any]]) -> None:
    OUT_PROMPT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PROMPT_LOG.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")



def format_pct(n: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{(100.0 * n / total):.1f}%"



def make_distribution_table(series: pd.Series, column_name: str) -> list[str]:
    counts = series.value_counts(dropna=False)
    total = int(counts.sum())
    lines = [f"| {column_name} | n | % |", "|---|---:|---:|"]
    for label, count in counts.items():
        lines.append(f"| {label} | {int(count)} | {format_pct(int(count), total)} |")
    return lines



def make_report(df: pd.DataFrame) -> str:
    total = len(df)
    cp_count = int((df["trigger_type"] == "cognitive_perturbation").sum())
    fr_count = int((df["trigger_type"] == "functional_reorientation").sum())

    sample_stats = {
        "sample_size": total,
        "distinct_meetings": int(df["meeting_id"].nunique()),
        "include_meetings": int(df.loc[df["quality_label"] == "include", "meeting_id"].nunique()),
        "include_with_caution_meetings": int(
            df.loc[df["quality_label"] == "include_with_caution", "meeting_id"].nunique()
        ),
        "joint_true": int(df["joint_corroborated"].sum()),
        "joint_false": int((~df["joint_corroborated"]).sum()),
        "middle_or_late": int(df["timing_bin"].isin(["middle", "late"]).sum()),
        "max_per_meeting": int(df["meeting_id"].value_counts().max()),
    }

    by_joint = (
        df.groupby(["joint_corroborated", "trigger_type"]).size().unstack(fill_value=0).reset_index()
    )
    by_quality = df.groupby(["quality_label", "trigger_type"]).size().unstack(fill_value=0).reset_index()

    ordered = df.sort_values("calibration_case_id").copy()

    lines: list[str] = []
    lines.append("# Step 05 calibration classification report\n")
    lines.append(
        f"This report documents the approved 20-case calibration run for Step 05. Each case was classified from a transcript window centered on the Entropy-UCL peak (`peak_second ± 180 s`), with the transcript kept in its source language and all output labels and justifications standardized in English. The purpose of this stage is to inspect the CP versus FR coding behavior before launching the remaining 156 classifications.\n"
    )

    lines.append("## Calibration sample coverage\n")
    lines.append("| Requirement | Target | Achieved |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Sample size | 20 | {sample_stats['sample_size']} |")
    lines.append(f"| Distinct meetings | 5 | {sample_stats['distinct_meetings']} |")
    lines.append(f"| Include meetings | 5 | {sample_stats['include_meetings']} |")
    lines.append(
        f"| Include-with-caution meetings | 2 | {sample_stats['include_with_caution_meetings']} |"
    )
    lines.append(f"| Joint corroborated = True | 8 | {sample_stats['joint_true']} |")
    lines.append(f"| Joint corroborated = False | 8 | {sample_stats['joint_false']} |")
    lines.append(f"| Middle or late events | 6 | {sample_stats['middle_or_late']} |")
    lines.append(f"| Max cases from one meeting | 2 | {sample_stats['max_per_meeting']} |\n")

    lines.append("## Trigger-type distribution\n")
    lines.extend(make_distribution_table(df["trigger_type"], "trigger_type"))
    lines.append("")
    lines.append(
        f"Across the approved calibration set, `cognitive_perturbation` accounts for {cp_count} cases ({format_pct(cp_count, total)}), whereas `functional_reorientation` accounts for {fr_count} cases ({format_pct(fr_count, total)}). This split provides an initial check on whether the Step 05 prompt is yielding a plausible separation between frame-disrupting episodes and coordination-oriented reorientation episodes.\n"
    )

    lines.append("## Trigger-subtype distribution\n")
    lines.extend(make_distribution_table(df["trigger_subtype"], "trigger_subtype"))
    lines.append("")

    lines.append("## SMM-dimension distribution\n")
    lines.extend(make_distribution_table(df["smm_dimension"], "smm_dimension"))
    lines.append("")

    lines.append("## Confidence distribution\n")
    lines.extend(make_distribution_table(df["confidence"], "confidence"))
    lines.append("")

    lines.append("## Trigger type by joint corroboration\n")
    lines.append("| joint_corroborated | cognitive_perturbation | functional_reorientation | total |")
    lines.append("|---|---:|---:|---:|")
    for _, row in by_joint.iterrows():
        cp = int(row.get("cognitive_perturbation", 0))
        fr = int(row.get("functional_reorientation", 0))
        total_row = cp + fr
        lines.append(f"| {bool(row['joint_corroborated'])} | {cp} | {fr} | {total_row} |")
    lines.append("")

    lines.append("## Trigger type by meeting quality\n")
    lines.append("| quality_label | cognitive_perturbation | functional_reorientation | total |")
    lines.append("|---|---:|---:|---:|")
    for _, row in by_quality.iterrows():
        cp = int(row.get("cognitive_perturbation", 0))
        fr = int(row.get("functional_reorientation", 0))
        total_row = cp + fr
        lines.append(f"| {row['quality_label']} | {cp} | {fr} | {total_row} |")
    lines.append("")

    lines.append("## Case-level classifications\n")
    lines.append(
        "| calibration_case_id | meeting_id | peak_second | timing_bin | joint_corroborated | trigger_type | trigger_subtype | smm_dimension | confidence |"
    )
    lines.append("|---|---|---:|---|---|---|---|---|---|")
    for _, row in ordered.iterrows():
        lines.append(
            f"| {row['calibration_case_id']} | {row['meeting_id']} | {int(row['peak_second'])} | {row['timing_bin']} | {bool(row['joint_corroborated'])} | {row['trigger_type']} | {row['trigger_subtype']} | {row['smm_dimension']} | {row['confidence']} |"
        )
    lines.append("")

    lines.append("## Case-level summaries and justifications\n")
    lines.append(
        "| calibration_case_id | content_summary | justification |"
    )
    lines.append("|---|---|---|")
    for _, row in ordered.iterrows():
        summary = str(row["content_summary"]).replace("|", "\\|")
        justification = str(row["justification"]).replace("|", "\\|")
        lines.append(f"| {row['calibration_case_id']} | {summary} | {justification} |")
    lines.append("")

    lines.append("## Operational note\n")
    lines.append(
        "The pipeline stops here by design. The remaining 156 Entropy-UCL events should not be classified until this calibration report is reviewed and explicitly approved."
    )

    return "\n".join(lines) + "\n"



def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = load_sample()
    client = OpenAI(base_url=OPENAI_BASE_URL)

    transcript_cache: dict[str, pd.DataFrame | None] = {}
    classifications: list[dict[str, Any]] = []
    prompt_log: list[dict[str, Any]] = []

    for idx, row in sample.iterrows():
        meeting_id = str(row["meeting_id"])
        if meeting_id not in transcript_cache:
            transcript_path = find_transcript_path(meeting_id)
            transcript_cache[meeting_id] = load_transcript(transcript_path) if transcript_path else None

        payload = build_payload(row, transcript_cache[meeting_id])
        classification, log_record = classify_case(client, payload)
        classifications.append(classification)
        prompt_log.append(log_record)
        print(f"Classified {idx + 1} / {len(sample)}: {payload.calibration_case_id} ({payload.meeting_id})")
        time.sleep(SLEEP_BETWEEN_CALLS)

    df = pd.DataFrame(classifications).sort_values("calibration_case_id").reset_index(drop=True)
    df.to_csv(OUT_CSV, index=False)
    save_prompt_log(prompt_log)
    OUT_REPORT.write_text(make_report(df), encoding="utf-8")

    cp_count = int((df["trigger_type"] == "cognitive_perturbation").sum())
    fr_count = int((df["trigger_type"] == "functional_reorientation").sum())
    print(f"Completed calibration run: CP={cp_count}, FR={fr_count}, output={OUT_CSV}")
    print(f"Report written to {OUT_REPORT}")


if __name__ == "__main__":
    main()
