#!/usr/bin/env python3
from __future__ import annotations

import json
import math
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
    raise SystemExit(
        "The openai package is required. Install it with: sudo pip3 install openai"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INFLECTION_POINTS_CSV = PROJECT_ROOT / "data/processed/inflection_points/inflection_points.csv"
TRANSCRIPT_DIR = PROJECT_ROOT / "data/anonymized"
OUTPUT_DIR = PROJECT_ROOT / "data/processed/llm_classification"
OUTPUT_CSV = OUTPUT_DIR / "llm_classifications.csv"
CHECKPOINT_CSV = OUTPUT_DIR / "llm_classifications_checkpoint.csv"
CONSOLE_LOG = OUTPUT_DIR / "step05_console_summary.txt"

CONTEXT_BEFORE = 120
CONTEXT_AFTER = 120
BATCH_SIZE = 10
SLEEP_BETWEEN_BATCHES = 2
CHECKPOINT_EVERY = 50
MODEL = os.environ.get("STEP05_MODEL", "gpt-4.1-mini")
MAX_RETRIES = 3
TEMPERATURE = 0

OUTPUT_COLUMNS = [
    "meeting_id",
    "peak_second",
    "onset_second",
    "offset_second",
    "combined_delta",
    "smm_impact",
    "smm_dimension",
    "smm_perturbation",
    "perturbation_type",
    "trigger_content_summary",
    "confidence",
    "segment_n_turns",
    "segment_duration_seconds",
]

VALID_IMPACTS = {"disrupts", "proposes", "updates", "neutral"}
VALID_DIMENSIONS = {"task_understanding", "strategy", "roles", "constraints", "goals", "none"}
VALID_PERTURBATION_TYPES = {
    "factual_correction",
    "role_challenge",
    "goal_reframe",
    "constraint_revelation",
    "generative_tension",
    "none",
}
VALID_CONFIDENCE = {"high", "medium", "low"}

SYSTEM_PROMPT = """You are analyzing a segment of a startup team meeting transcript. A communication dynamics algorithm detected unusual structural change in the communication pattern around the marked time. Your task is to classify what happened.

Classify using these rules:

smm_impact:
- \"disrupts\": content that challenges, contradicts, or invalidates an existing shared understanding
- \"proposes\": content that introduces a new idea, option, or direction not previously on the table
- \"updates\": content that refines, elaborates, or advances an existing shared understanding without challenging it
- \"neutral\": no clear impact on shared mental model (logistics, off-topic, pure social talk)

smm_dimension (which aspect of the shared mental model was affected):
- \"task_understanding\": how the team understands what they're doing and why
- \"strategy\": how they plan to achieve their goals
- \"roles\": who is responsible for what
- \"constraints\": time, resources, or external limitations
- \"goals\": what they are trying to achieve
- \"none\": no SMM dimension affected

smm_perturbation: true if smm_impact is \"disrupts\" OR \"proposes\", false otherwise

perturbation_type (only if smm_perturbation is true):
- \"factual_correction\": new information that corrects a mistaken shared assumption
- \"role_challenge\": challenge to who does what or who has authority
- \"goal_reframe\": reframe of what the team should be optimizing for
- \"constraint_revelation\": new limitation or restriction that changes the possibility space
- \"generative_tension\": creative disagreement or competing proposal that opens exploration
  (use this when there's a proposal AND a counter-proposal/disagreement in the same episode,
   OR when the proposal is explicitly evaluative/comparative)

confidence:
- \"high\": clear, unambiguous classification
- \"medium\": classification reasonable but the segment is ambiguous
- \"low\": insufficient context or too fragmented to classify reliably

You MUST return exactly one JSON object with these keys:
- meeting_id
- peak_second
- smm_impact
- smm_dimension
- smm_perturbation
- perturbation_type
- trigger_content_summary
- confidence

The field trigger_content_summary MUST be a non-empty English sentence of 8-30 words describing the specific content that drove the structural change. Never leave it blank, never use null, and never omit the key.

Return ONLY valid JSON. No explanations outside the JSON."""


@dataclass
class SegmentPayload:
    meeting_id: str
    onset_second: int
    offset_second: int
    peak_second: int
    combined_delta: float | None
    segment_text: str
    segment_n_turns: int
    segment_duration_seconds: int


def load_inflection_points() -> pd.DataFrame:
    df = pd.read_csv(INFLECTION_POINTS_CSV)
    required = {"meeting_id", "onset_second", "offset_second", "peak_second", "combined_delta"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in inflection_points.csv: {sorted(missing)}")
    return df.sort_values(["meeting_id", "peak_second"]).reset_index(drop=True)


def find_transcript_path(meeting_id: str) -> Path | None:
    candidates = [
        TRANSCRIPT_DIR / meeting_id / f"{meeting_id}_transcript.csv",
        TRANSCRIPT_DIR / "startup" / f"{meeting_id}_transcript.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
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
        raise ValueError(f"No onset_seconds-like column found in {transcript_path}")

    speaker_col = None
    for candidate in ["speaker_id", "speaker", "speaker_label", "participant", "role"]:
        if candidate in normalized:
            speaker_col = normalized[candidate]
            break
    if speaker_col is None:
        raise ValueError(f"No speaker column found in {transcript_path}")

    text_col = None
    for candidate in ["text", "utterance", "transcript", "content"]:
        if candidate in normalized:
            text_col = normalized[candidate]
            break
    if text_col is None:
        raise ValueError(f"No text column found in {transcript_path}")

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


def build_segment_payload(row: pd.Series, transcript: pd.DataFrame) -> SegmentPayload:
    peak_second = int(row["peak_second"])
    start_second = max(0, peak_second - CONTEXT_BEFORE)
    end_second = peak_second + CONTEXT_AFTER

    segment = transcript[
        transcript["onset_seconds"].between(start_second, end_second, inclusive="both")
    ].copy()
    segment = segment.sort_values("onset_seconds")

    lines = [
        f"[Speaker {speaker}, t={int(onset)}s]: {text}"
        for onset, speaker, text in segment[["onset_seconds", "speaker_id", "text"]].itertuples(index=False, name=None)
    ]
    segment_text = "\n".join(lines)

    return SegmentPayload(
        meeting_id=str(row["meeting_id"]),
        onset_second=int(row["onset_second"]),
        offset_second=int(row["offset_second"]),
        peak_second=peak_second,
        combined_delta=coerce_float(row.get("combined_delta")),
        segment_text=segment_text,
        segment_n_turns=int(len(segment)),
        segment_duration_seconds=int(end_second - start_second),
    )


def coerce_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
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


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def build_fallback_summary(payload: SegmentPayload) -> str:
    if not payload.segment_text.strip():
        return "No transcript content was available in the selected context window."

    lines = [line.strip() for line in payload.segment_text.splitlines() if line.strip()]
    if not lines:
        return "No transcript content was available in the selected context window."

    selected = lines[:2]
    cleaned = []
    for line in selected:
        line = re.sub(r"^\[Speaker\s+[^\]]+\]:\s*", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            cleaned.append(line)

    if not cleaned:
        return "The detected episode contained transcript content, but no concise trigger summary was returned."

    summary = " / ".join(cleaned)
    if len(summary) > 220:
        summary = summary[:217].rstrip() + "..."
    return summary


def sanitize_classification(raw: dict[str, Any], payload: SegmentPayload) -> dict[str, Any]:
    impact = str(raw.get("smm_impact", "neutral")).strip().lower()
    if impact not in VALID_IMPACTS:
        impact = "neutral"

    dimension = str(raw.get("smm_dimension", "none")).strip().lower()
    if dimension not in VALID_DIMENSIONS:
        dimension = "none"

    perturbation = normalize_bool(raw.get("smm_perturbation", impact in {"disrupts", "proposes"}))
    if impact in {"disrupts", "proposes"}:
        perturbation = True

    perturbation_type = str(raw.get("perturbation_type", "none")).strip().lower()
    if perturbation_type not in VALID_PERTURBATION_TYPES:
        perturbation_type = "none"
    if not perturbation:
        perturbation_type = "none"

    summary = str(raw.get("trigger_content_summary", "")).strip()
    if not summary:
        summary = build_fallback_summary(payload)

    confidence = str(raw.get("confidence", "medium")).strip().lower()
    if confidence not in VALID_CONFIDENCE:
        confidence = "medium"
    if payload.segment_n_turns < 3:
        confidence = "low"

    return {
        "meeting_id": payload.meeting_id,
        "peak_second": payload.peak_second,
        "onset_second": payload.onset_second,
        "offset_second": payload.offset_second,
        "combined_delta": payload.combined_delta,
        "smm_impact": impact,
        "smm_dimension": dimension,
        "smm_perturbation": perturbation,
        "perturbation_type": perturbation_type,
        "trigger_content_summary": summary,
        "confidence": confidence,
        "segment_n_turns": payload.segment_n_turns,
        "segment_duration_seconds": payload.segment_duration_seconds,
    }


def build_user_prompt(payload: SegmentPayload) -> str:
    return (
        f"Meeting ID: {payload.meeting_id}\n"
        f"Peak second: {payload.peak_second}\n"
        f"Inflection interval: {payload.onset_second}-{payload.offset_second}\n"
        f"Combined delta: {payload.combined_delta}\n"
        f"Context window: {CONTEXT_BEFORE} seconds before peak and {CONTEXT_AFTER} seconds after peak\n"
        f"Number of transcript turns in segment: {payload.segment_n_turns}\n\n"
        "Return a JSON object using this exact schema:\n"
        "{\n"
        '  \"meeting_id\": \"' + payload.meeting_id + '\",\n'
        '  \"peak_second\": ' + str(payload.peak_second) + ',\n'
        '  \"smm_impact\": \"disrupts | proposes | updates | neutral\",\n'
        '  \"smm_dimension\": \"task_understanding | strategy | roles | constraints | goals | none\",\n'
        '  \"smm_perturbation\": true,\n'
        '  \"perturbation_type\": \"factual_correction | role_challenge | goal_reframe | constraint_revelation | generative_tension | none\",\n'
        '  \"trigger_content_summary\": \"One English sentence describing the specific content that drove the structural change\",\n'
        '  \"confidence\": \"high | medium | low\"\n'
        "}\n\n"
        "Important constraints:\n"
        "- Keep trigger_content_summary in English even if the transcript is in Portuguese.\n"
        "- trigger_content_summary must be non-empty and specific.\n"
        "- If smm_impact is updates or neutral, set smm_perturbation to false and perturbation_type to none.\n"
        "- If smm_impact is disrupts or proposes, set smm_perturbation to true.\n\n"
        "Transcript segment:\n"
        f"{payload.segment_text if payload.segment_text else '[No transcript turns in selected window]'}"
    )


def classify_with_llm(client: OpenAI, payload: SegmentPayload) -> dict[str, Any]:
    user_prompt = build_user_prompt(payload)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.responses.create(
                model=MODEL,
                temperature=TEMPERATURE,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw_text = response.output_text
            parsed = json.loads(extract_json_candidate(raw_text))
            if not isinstance(parsed, dict):
                raise ValueError("Model response JSON is not an object")
            return sanitize_classification(parsed, payload)
        except Exception as exc:  # pragma: no cover - runtime API robustness
            last_error = exc
            time.sleep(min(attempt, 3))

    return {
        "meeting_id": payload.meeting_id,
        "peak_second": payload.peak_second,
        "onset_second": payload.onset_second,
        "offset_second": payload.offset_second,
        "combined_delta": payload.combined_delta,
        "smm_impact": "parse_error",
        "smm_dimension": "none",
        "smm_perturbation": False,
        "perturbation_type": "none",
        "trigger_content_summary": f"LLM parse failure: {last_error}",
        "confidence": "low",
        "segment_n_turns": payload.segment_n_turns,
        "segment_duration_seconds": payload.segment_duration_seconds,
    }


def save_results(records: list[dict[str, Any]], path: Path) -> None:
    df = pd.DataFrame(records)
    for column in OUTPUT_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    df = df[OUTPUT_COLUMNS].sort_values(["meeting_id", "peak_second"]).reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def existing_keys(path: Path) -> set[tuple[str, int]]:
    if not path.exists():
        return set()
    df = pd.read_csv(path)
    if "meeting_id" not in df.columns or "peak_second" not in df.columns:
        return set()
    keys = set()
    for meeting_id, peak_second in df[["meeting_id", "peak_second"]].itertuples(index=False, name=None):
        try:
            keys.add((str(meeting_id), int(peak_second)))
        except Exception:
            continue
    return keys


def render_console_report(df: pd.DataFrame) -> str:
    total = len(df)
    parse_errors = int((df["smm_impact"] == "parse_error").sum()) if total else 0
    no_transcript = int((df["smm_impact"] == "no_transcript").sum()) if total else 0
    low_conf = int((df["confidence"] == "low").sum()) if total else 0
    successful = total - parse_errors - no_transcript

    def pct(n: int, d: int) -> str:
        return f"{(100.0 * n / d):.1f}%" if d else "0.0%"

    lines = [
        "=== Step 5: LLM Event Classification ===",
        f"Total inflection points processed: {total}",
        f"Successful classifications: {successful}",
        f"Parse errors: {parse_errors}",
        f"No transcript: {no_transcript}",
        f"Low confidence: {low_conf} ({pct(low_conf, total)})",
        "",
        "smm_impact distribution:",
    ]

    impact_order = ["disrupts", "proposes", "updates", "neutral", "parse_error", "no_transcript"]
    for label in impact_order:
        n = int((df["smm_impact"] == label).sum()) if total else 0
        lines.append(f"  {label}: {n} ({pct(n, total)})")

    true_count = int((df["smm_perturbation"] == True).sum()) if total else 0
    false_count = int((df["smm_perturbation"] == False).sum()) if total else 0
    lines.extend(
        [
            "",
            "smm_perturbation:",
            f"  TRUE: {true_count} ({pct(true_count, total)}) -> candidate triggers",
            f"  FALSE: {false_count} ({pct(false_count, total)})",
            "",
            "perturbation_type distribution (among TRUE):",
        ]
    )

    true_df = df[df["smm_perturbation"] == True].copy()
    true_total = len(true_df)
    for label in [
        "factual_correction",
        "role_challenge",
        "goal_reframe",
        "constraint_revelation",
        "generative_tension",
    ]:
        n = int((true_df["perturbation_type"] == label).sum()) if true_total else 0
        lines.append(f"  {label}: {n} ({pct(n, true_total)})")

    lines.extend(["", "confidence distribution:"])
    for label in ["high", "medium", "low"]:
        n = int((df["confidence"] == label).sum()) if total else 0
        lines.append(f"  {label}: {n} ({pct(n, total)})")

    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OpenAI()

    inflection_points = load_inflection_points()
    processed_keys = existing_keys(CHECKPOINT_CSV)
    records: list[dict[str, Any]] = []

    if CHECKPOINT_CSV.exists():
        records = pd.read_csv(CHECKPOINT_CSV).to_dict(orient="records")

    transcript_cache: dict[str, pd.DataFrame | None] = {}
    processed_since_checkpoint = 0

    for index, row in inflection_points.iterrows():
        key = (str(row["meeting_id"]), int(row["peak_second"]))
        if key in processed_keys:
            continue

        meeting_id = str(row["meeting_id"])
        if meeting_id not in transcript_cache:
            transcript_path = find_transcript_path(meeting_id)
            transcript_cache[meeting_id] = load_transcript(transcript_path) if transcript_path else None

        transcript = transcript_cache[meeting_id]

        if transcript is None:
            result = {
                "meeting_id": meeting_id,
                "peak_second": int(row["peak_second"]),
                "onset_second": int(row["onset_second"]),
                "offset_second": int(row["offset_second"]),
                "combined_delta": coerce_float(row.get("combined_delta")),
                "smm_impact": "no_transcript",
                "smm_dimension": "none",
                "smm_perturbation": False,
                "perturbation_type": "none",
                "trigger_content_summary": "Transcript file not found for this meeting.",
                "confidence": "low",
                "segment_n_turns": 0,
                "segment_duration_seconds": CONTEXT_BEFORE + CONTEXT_AFTER,
            }
        else:
            payload = build_segment_payload(row, transcript)
            result = classify_with_llm(client, payload)

        records.append(result)
        processed_keys.add(key)
        processed_since_checkpoint += 1

        if processed_since_checkpoint % CHECKPOINT_EVERY == 0:
            save_results(records, CHECKPOINT_CSV)

        if processed_since_checkpoint % BATCH_SIZE == 0:
            time.sleep(SLEEP_BETWEEN_BATCHES)

        if (index + 1) % 25 == 0:
            print(f"Processed {index + 1} / {len(inflection_points)} inflection points")

    save_results(records, CHECKPOINT_CSV)
    save_results(records, OUTPUT_CSV)

    final_df = pd.read_csv(OUTPUT_CSV)
    report = render_console_report(final_df)
    CONSOLE_LOG.write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
