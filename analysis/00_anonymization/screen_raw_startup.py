from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path('/home/ubuntu/small-groups-comm-metrics')
RAW_DIR = ROOT / 'data' / 'raw' / 'startup'
OUT_CSV = ROOT / 'analysis' / '00_anonymization' / 'startup_raw_screening.csv'

LINE_RE = re.compile(r'^(?P<time>\d{1,2}:\d{2})\s+(?P<speaker>[^:]{1,120}):\s*(?P<text>.*\S.*)$')
NOISE_PATTERNS = [
    re.compile(r'\bbonjour\b', re.I),
    re.compile(r'\bjennifer what more genius today\b', re.I),
    re.compile(r'\bpokemon\b', re.I),
    re.compile(r'\bbusiness\.? actually\b', re.I),
]
PT_HINTS = {
    'que','não','pra','gente','produto','cliente','empresa','mercado','venda','vendas',
    'bateria','parceria','time','projeto','cara','acho','porque','depois','agora','então',
}
EN_HINTS = {
    'the','and','is','are','with','this','that','for','what','today','business','product',
}


def assess_file(path: Path) -> dict:
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    parsed = []
    for ln in lines:
        m = LINE_RE.match(ln)
        if m:
            parsed.append(m.groupdict())
    parsed_count = len(parsed)
    unique_speakers = len({row['speaker'] for row in parsed})
    total_text = ' '.join(row['text'] for row in parsed)
    words = re.findall(r"[A-Za-zÀ-ÿ']+", total_text.lower())
    word_count = len(words)
    pt_hits = sum(1 for w in words if w in PT_HINTS)
    en_hits = sum(1 for w in words if w in EN_HINTS)
    noise_hits = sum(len(p.findall(total_text)) for p in NOISE_PATTERNS)
    replacement_chars = text.count('�')
    avg_words_per_turn = round(word_count / parsed_count, 2) if parsed_count else 0.0
    speaker_top = Counter(row['speaker'] for row in parsed).most_common(3)
    status = 'usable'
    reason = ''
    if path.name == 'pasted_content.txt':
        status = 'exclude'
        reason = 'Non-transcript instruction file copied with uploads.'
    elif '2025.03.10xPulsoUltraCharge' in path.name:
        status = 'exclude'
        reason = 'Known corrupted transcript with unstable transcription language and low analytical reliability.'
    elif '2025.03.02PulsoE-life' in path.name:
        status = 'exclude'
        reason = 'Known corrupted transcript with nonsensical transcription output and low analytical reliability.'
    elif parsed_count < 10:
        status = 'review'
        reason = 'Very few parseable turns.'
    elif noise_hits >= 2 and pt_hits < 20:
        status = 'exclude'
        reason = 'Transcript appears dominated by transcription noise rather than meaningful meeting content.'
    elif avg_words_per_turn < 2:
        status = 'review'
        reason = 'Turns are too short to support analysis.'

    return {
        'file_name': path.name,
        'parsed_turns': parsed_count,
        'unique_speakers': unique_speakers,
        'word_count': word_count,
        'avg_words_per_turn': avg_words_per_turn,
        'pt_hint_hits': pt_hits,
        'en_hint_hits': en_hits,
        'noise_pattern_hits': noise_hits,
        'replacement_characters': replacement_chars,
        'top_speakers': '; '.join(f'{spk} ({n})' for spk, n in speaker_top),
        'status': status,
        'reason': reason,
    }


def main() -> None:
    rows = [assess_file(path) for path in sorted(RAW_DIR.glob('*.txt'))]
    with OUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {OUT_CSV}')
    for row in rows:
        print(f"{row['status']:>7} | {row['file_name']} | turns={row['parsed_turns']} | words={row['word_count']} | reason={row['reason']}")


if __name__ == '__main__':
    main()
