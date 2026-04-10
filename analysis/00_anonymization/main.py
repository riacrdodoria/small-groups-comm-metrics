from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

RAW_DIR = Path('data/raw/startup')
ENTITY_LIST = Path('data/raw/entity_list.csv')
ANON_DIR = Path('data/anonymized/startup')
REVIEW_FILE = ANON_DIR / 'review_flagged.csv'
SPACY_MODEL_PT = 'pt_core_news_lg'
SPACY_MODEL_EN = 'en_core_web_lg'
EXCLUDED_FILES = {
    '2025.03.10xPulsoUltraCharge.txt': 'Corrupted transcript with unstable transcription language and insufficient usable structure.',
    '2025.03.02PulsoE-life.txt': 'Corrupted transcript dominated by nonsensical transcription output.',
    'pasted_content.txt': 'Instruction file accidentally included with uploads; not a meeting transcript.',
}
ENTITY_LABELS = {'PER', 'PERSON', 'ORG', 'LOC', 'GPE'}
LINE_RE = re.compile(r'^(?P<clock>\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<speaker>[^:]{1,150}):\s*(?P<text>.*\S.*)$')
ANON_TOKEN_RE = re.compile(r'^[A-Z]+_[A-Z0-9]+$')
IGNORE_NER_TEXTS = {
    'tipo', 'claro', 'certo', 'pera', 'nossa', 'poxa', 'startup', 'baterias', 'frota',
    'extra', 'janeiro', 'ids', 'excelzinho', 'gil', 'zé', 'exu', 'fulano', 'marte',
    'ronaldo', 'francisco', 'gabriel', 'irineu', 'patrícia'
}
TYPE_PREFIX = {
    'startup': 'STARTUP',
    'client': 'CLIENT',
    'partner': 'PARTNER',
    'supplier': 'PARTNER',
    'investor': 'INVESTOR',
    'vc': 'INVESTOR',
    'department': 'DEPT',
    'team': 'DEPT',
    'product': 'PRODUCT',
    'service': 'PRODUCT',
    'person': 'PERSON',
    'location': 'LOCATION',
}


@dataclass
class EntityRule:
    original: str
    replacement: str
    type: str
    regex: re.Pattern[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run Step 0 anonymization for startup meeting transcripts.')
    parser.add_argument('--force', action='store_true', help='Overwrite existing anonymized outputs.')
    return parser.parse_args()


def ensure_entity_list_exists() -> None:
    if ENTITY_LIST.exists():
        return
    ENTITY_LIST.parent.mkdir(parents=True, exist_ok=True)
    seed_rows = [
        {'original': 'UltraCharge', 'replacement': '[STARTUP_A]', 'type': 'startup'},
        {'original': 'Ultra Charge', 'replacement': '[STARTUP_A]', 'type': 'startup'},
        {'original': 'E-life', 'replacement': '[STARTUP_B]', 'type': 'startup'},
        {'original': 'Elife', 'replacement': '[STARTUP_B]', 'type': 'startup'},
        {'original': 'E life', 'replacement': '[STARTUP_B]', 'type': 'startup'},
        {'original': 'Ricardo José Dória', 'replacement': '[PERSON_A]', 'type': 'person'},
        {'original': 'Ricardo', 'replacement': '[PERSON_A]', 'type': 'person'},
        {'original': 'Pedro Battistini', 'replacement': '[PERSON_B]', 'type': 'person'},
        {'original': 'Pedro', 'replacement': '[PERSON_B]', 'type': 'person'},
        {'original': 'Giovane Souza', 'replacement': '[PERSON_C]', 'type': 'person'},
        {'original': 'Giovane', 'replacement': '[PERSON_C]', 'type': 'person'},
        {'original': 'Tayná Fernandes', 'replacement': '[PERSON_D]', 'type': 'person'},
        {'original': 'Tayná', 'replacement': '[PERSON_D]', 'type': 'person'},
        {'original': 'Scania', 'replacement': '[PARTNER_A]', 'type': 'partner'},
        {'original': 'Volkswagen', 'replacement': '[PARTNER_B]', 'type': 'partner'},
        {'original': 'Volks', 'replacement': '[PARTNER_B]', 'type': 'partner'},
        {'original': 'Volvo', 'replacement': '[PARTNER_C]', 'type': 'partner'},
        {'original': 'WEG', 'replacement': '[PARTNER_D]', 'type': 'partner'},
        {'original': 'Google', 'replacement': '[PARTNER_E]', 'type': 'partner'},
        {'original': 'Claro', 'replacement': '[PARTNER_F]', 'type': 'partner'},
        {'original': 'Copel', 'replacement': '[PARTNER_G]', 'type': 'partner'},
        {'original': 'estapar', 'replacement': '[CLIENT_A]', 'type': 'client'},
        {'original': 'Brasil', 'replacement': '[LOCATION_A]', 'type': 'location'},
        {'original': 'São Paulo', 'replacement': '[LOCATION_B]', 'type': 'location'},
        {'original': 'São Bernardo', 'replacement': '[LOCATION_C]', 'type': 'location'},
        {'original': 'Curitiba', 'replacement': '[LOCATION_D]', 'type': 'location'},
        {'original': 'Suécia', 'replacement': '[LOCATION_E]', 'type': 'location'},
        {'original': 'China', 'replacement': '[LOCATION_F]', 'type': 'location'},
    ]
    with ENTITY_LIST.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['original', 'replacement', 'type'])
        writer.writeheader()
        writer.writerows(seed_rows)


def load_entity_rules() -> list[EntityRule]:
    ensure_entity_list_exists()
    df = pd.read_csv(ENTITY_LIST)
    required = {'original', 'replacement', 'type'}
    if not required.issubset(df.columns):
        raise ValueError(f'entity_list.csv must contain columns {sorted(required)}')
    rules: list[EntityRule] = []
    for row in df.fillna('').to_dict(orient='records'):
        original = str(row['original']).strip()
        replacement = str(row['replacement']).strip()
        entity_type = str(row['type']).strip().lower()
        if not original or not replacement or not entity_type:
            continue
        regex = re.compile(rf'(?<!\w){re.escape(original)}(?!\w)', re.IGNORECASE)
        rules.append(EntityRule(original=original, replacement=replacement, type=entity_type, regex=regex))
    rules.sort(key=lambda r: len(r.original), reverse=True)
    return rules


def clock_to_seconds(value: str) -> float:
    parts = [int(p) for p in value.split(':')]
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes * 60 + seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours * 3600 + minutes * 60 + seconds)
    raise ValueError(f'Unrecognized time value: {value}')


def normalize_meeting_id(path: Path) -> str:
    stem = path.stem
    stem = stem.replace('Pulso', '').replace('Pulse', '')
    stem = stem.replace('UltraCharge', 'startup_a').replace('UltraCharge', 'startup_a')
    stem = stem.replace('E-life', 'startup_b').replace('Elife', 'startup_b')
    stem = stem.replace('startup_astartup_a', 'startup_a')
    stem = stem.replace('startup_bstartup_b', 'startup_b')
    stem = re.sub(r'\s+', '_', stem)
    stem = re.sub(r'[^A-Za-z0-9._-]+', '_', stem)
    stem = stem.strip('_')
    return stem


def load_raw_meeting(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == '.csv':
        df = pd.read_csv(path)
        expected = {'onset_seconds', 'speaker_id', 'text'}
        if not expected.issubset(df.columns):
            raise ValueError(f'{path.name} is missing expected columns {sorted(expected)}')
        return df[list(expected)].copy()

    rows = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        match = LINE_RE.match(line)
        if not match:
            continue
        rows.append(
            {
                'onset_seconds': clock_to_seconds(match.group('clock')),
                'speaker_id': match.group('speaker').strip(),
                'text': match.group('text').strip(),
            }
        )
    if not rows:
        raise ValueError(f'No parseable meeting turns found in {path.name}')
    return pd.DataFrame(rows)


def anonymize_speakers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    speaker_map: dict[str, int] = {}
    anon_ids: list[int] = []
    next_id = 1
    for speaker in df['speaker_id'].astype(str):
        if speaker not in speaker_map:
            speaker_map[speaker] = next_id
            next_id += 1
        anon_ids.append(speaker_map[speaker])
    out = df.copy()
    out['speaker_id'] = anon_ids
    map_df = pd.DataFrame(
        [{'original_speaker_id': k, 'anonymous_speaker_id': v} for k, v in speaker_map.items()]
    )
    return out, map_df


def apply_entity_rules(text: str, rules: Iterable[EntityRule]) -> tuple[str, list[dict[str, str]]]:
    updated = text
    replacements: list[dict[str, str]] = []
    for rule in rules:
        count = len(rule.regex.findall(updated))
        if count:
            updated = rule.regex.sub(rule.replacement, updated)
            replacements.append(
                {
                    'original': rule.original,
                    'replacement': rule.replacement,
                    'type': rule.type,
                    'count': str(count),
                }
            )
    return updated, replacements


def load_spacy_model(model_name: str):
    import spacy

    try:
        return spacy.load(model_name)
    except OSError as exc:
        raise RuntimeError(
            f'SpaCy model {model_name} is not installed. Install it before running Step 0.'
        ) from exc


def detect_language(text: str) -> str:
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0
    try:
        lang = detect(text[:10000]) if text.strip() else 'pt'
    except Exception:
        lang = 'pt'
    return 'en' if lang.startswith('en') else 'pt'


def replace_unresolved_entities(text: str, nlp, meeting_id: str, onset_seconds: float) -> tuple[str, list[dict[str, str]]]:
    doc = nlp(text)
    replacements: list[dict[str, str]] = []
    spans = []
    for ent in doc.ents:
        if ent.label_ not in ENTITY_LABELS:
            continue
        stripped = ent.text.strip()
        normalized = stripped.strip('[]')
        if not stripped:
            continue
        if '[' in ent.text and ']' in ent.text:
            continue
        if ANON_TOKEN_RE.match(normalized):
            continue
        if normalized.lower() in IGNORE_NER_TEXTS:
            continue
        spans.append((ent.start_char, ent.end_char, stripped, ent.label_))
    if not spans:
        return text, replacements

    updated_parts = []
    last = 0
    for start, end, ent_text, ent_label in sorted(spans, key=lambda x: x[0]):
        if start < last:
            continue
        updated_parts.append(text[last:start])
        updated_parts.append('[UNRESOLVED_ENTITY]')
        last = end
        context = extract_context(text, start, end)
        replacements.append(
            {
                'meeting_id': meeting_id,
                'onset_seconds': f'{onset_seconds:.2f}',
                'entity_text': ent_text,
                'entity_label': ent_label,
                'context': context,
            }
        )
    updated_parts.append(text[last:])
    return ''.join(updated_parts), replacements


def extract_context(text: str, start: int, end: int, window: int = 15) -> str:
    left_words = re.findall(r'\S+', text[:start])[-window:]
    entity_words = re.findall(r'\S+', text[start:end])
    right_words = re.findall(r'\S+', text[end:])[:window]
    return ' '.join(left_words + entity_words + right_words)


def save_entity_map(path: Path, entity_rows: list[dict[str, str]]) -> None:
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['original', 'replacement', 'type', 'count'])
        writer.writeheader()
        writer.writerows(entity_rows)


def main() -> None:
    args = parse_args()
    ANON_DIR.mkdir(parents=True, exist_ok=True)

    rules = load_entity_rules()
    pt_nlp = load_spacy_model(SPACY_MODEL_PT)
    en_nlp = load_spacy_model(SPACY_MODEL_EN)

    all_flagged: list[dict[str, str]] = []
    total_processed = 0
    total_replacements = Counter()
    total_exclusions = []

    for path in sorted(RAW_DIR.iterdir()):
        if path.is_dir():
            continue
        if path.name in EXCLUDED_FILES:
            total_exclusions.append({'file_name': path.name, 'reason': EXCLUDED_FILES[path.name]})
            continue
        if path.suffix.lower() not in {'.txt', '.csv'}:
            continue

        meeting_id = normalize_meeting_id(path)
        lsh_output = ANON_DIR / f'{meeting_id}_lsh_input.csv'
        transcript_output = ANON_DIR / f'{meeting_id}_transcript.csv'
        speaker_map_output = ANON_DIR / f'{meeting_id}_speaker_map.csv'
        entity_map_output = ANON_DIR / f'{meeting_id}_entity_map.csv'
        if not args.force and lsh_output.exists() and transcript_output.exists():
            raise FileExistsError(f'Outputs already exist for {meeting_id}. Re-run with --force to overwrite.')

        raw_df = load_raw_meeting(path)
        speaker_df, speaker_map_df = anonymize_speakers(raw_df)
        redacted_df = speaker_df.copy()
        language = detect_language(' '.join(raw_df['text'].astype(str).head(200).tolist()))
        nlp = en_nlp if language == 'en' else pt_nlp

        entity_map_rows: list[dict[str, str]] = []
        updated_texts = []
        for row in redacted_df.itertuples(index=False):
            replaced_text, replacements = apply_entity_rules(str(row.text), rules)
            for item in replacements:
                total_replacements[item['type']] += int(item['count'])
            entity_map_rows.extend(replacements)
            final_text, flagged = replace_unresolved_entities(
                replaced_text, nlp, meeting_id=meeting_id, onset_seconds=float(row.onset_seconds)
            )
            all_flagged.extend(flagged)
            updated_texts.append(final_text)
        redacted_df['text'] = updated_texts

        lsh_df = redacted_df[['onset_seconds', 'speaker_id']].copy()
        lsh_df.to_csv(lsh_output, index=False)
        redacted_df.to_csv(transcript_output, index=False)
        speaker_map_df.to_csv(speaker_map_output, index=False)
        save_entity_map(entity_map_output, entity_map_rows)
        total_processed += 1

    review_fields = ['meeting_id', 'onset_seconds', 'entity_text', 'entity_label', 'context']
    with REVIEW_FILE.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=review_fields)
        writer.writeheader()
        writer.writerows(all_flagged)

    exclusions_path = ANON_DIR / 'startup_sample_exclusions.json'
    exclusions_path.write_text(json.dumps(total_exclusions, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print(f'Meetings processed: {total_processed}')
    print(f'Excluded files: {len(total_exclusions)}')
    print(f'Remaining unresolved entities: {len(all_flagged)}')
    print('Entity replacements by type:')
    for entity_type, count in sorted(total_replacements.items()):
        print(f'  - {entity_type}: {count}')


if __name__ == '__main__':
    main()
