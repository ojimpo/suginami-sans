"""Shared static-font I/O. Canonical JSON and originals are read-only inputs."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ufoLib import UFOReader

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write_json(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recording_bounds(recording):
    pen = BoundsPen(None)
    recording.replay(pen)
    return pen.bounds


def read_ufo(path=None):
    config = read_json('source/font-config.json')
    reader = UFOReader(path or ROOT / config['ufo_path'], validate=True)
    info = SimpleNamespace()
    reader.readInfo(info)
    glyphset = reader.getGlyphSet()
    lib = reader.readLib()
    order = lib['public.glyphOrder']
    if set(order) != set(glyphset.keys()) or len(order) != len(set(order)):
        raise ValueError('UFO public.glyphOrder must contain each glyph exactly once')
    glyphs = {}
    for name in order:
        glyph = SimpleNamespace()
        glyphset.readGlyph(name, glyph)
        pen = RecordingPen()
        glyphset[name].draw(pen)
        glyphs[name] = (glyph, pen)
    features = reader.readFeatures()
    kerning = reader.readKerning()
    groups = reader.readGroups()
    reader.close()
    return config, info, order, glyphs, features, kerning, groups
