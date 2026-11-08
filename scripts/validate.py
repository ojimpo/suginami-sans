"""Validate source coverage, bounds, closed outlines and reproducibility metadata."""
from pathlib import Path
import json,csv,hashlib,math
from fontTools.svgLib.path import parse_path
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from glyph_source import load_source
ROOT=Path(__file__).resolve().parents[1]
d=load_source(); gs=d['glyphs']; codes=[g['unicode'] for g in gs.values() if g['unicode'] is not None]
assert len(codes)==len(set(codes))
assert all(ord(c) in codes for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ')
assert all(cp in codes for cp in range(32,127)) and 'y.alt' in gs
rows=[];report={}
for n,g in gs.items():
 p=BoundsPen(None);r=RecordingPen()
 for path in g['paths']:parse_path(path['d'],p);parse_path(path['d'],r)
 assert p.bounds is None or all(math.isfinite(v) for v in p.bounds)
 assert p.bounds is None or all(abs(a-b)<1e-7 for a,b in zip(p.bounds,g['bounds']))
 ops=[op for op,pts in r.value]
 assert ops.count('moveTo')==ops.count('closePath'),n
 report[n]={'contours':ops.count('moveTo'),'commands':len(ops),'bounds':g['bounds'],'fill_rules':sorted(set(p['fill_rule'] for p in g['paths'])),'role':g['reference_role']}
 rows.append([n,'' if g['unicode'] is None else f'U+{g["unicode"]:04X}',g['advance'],g['left_sidebearing'],g['right_sidebearing'],g['font_origin_shift_x']])
with (ROOT/'source/metrics-draft.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['glyph','unicode','advance_design_units','lsb_draft','rsb_draft','origin_shift_x']);w.writerows(rows)
(ROOT/'docs/glyph-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(f'PASS: {len(gs)} entries; {sum(bool(g["paths"]) for g in gs.values())} outlined glyphs + space; complete printable ASCII; unique Unicode; finite bounds; closed contours.')
print('NOT TESTED BY THIS SOURCE SCRIPT: overlap removal, winding conversion, hinting, interpolation, kerning, font output. See validate_fonts.py for static binary checks.')
