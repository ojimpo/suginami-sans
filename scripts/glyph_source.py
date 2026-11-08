"""Stdlib-only source merge: immutable imported outlines plus explicit additions."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def load_source():
    data = json.loads((ROOT / 'source/glyphs.json').read_text(encoding='utf-8'))
    extra_path = ROOT / 'source/additional-glyphs.json'
    if extra_path.exists():
        additions = json.loads(extra_path.read_text(encoding='utf-8'))['glyphs']
        overlap = set(data['glyphs']) & set(additions)
        if overlap:
            raise ValueError(f'Additions must not overwrite imported glyphs: {sorted(overlap)}')
        data['glyphs'].update(additions)
    codes = [g['unicode'] for g in data['glyphs'].values() if g['unicode'] is not None]
    if len(codes) != len(set(codes)):
        raise ValueError('Duplicate Unicode assignment in merged sources')
    return data
