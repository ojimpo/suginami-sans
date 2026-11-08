"""Generate neutral specimens and run current-font raster checks in a fresh clone."""
import html
import itertools
from PIL import Image, ImageDraw
from font_project import ROOT, read_json, write_json, sha256
from glyph_source import load_source
from raster import render_text
from topology import holes

def main():
    output = ROOT / 'proofs'
    output.mkdir(exist_ok=True)
    config = read_json('source/font-config.json')
    expected = read_json('source/expected-counters.json')
    source = load_source()['glyphs']
    records, phases, clipping = [], [], 0
    samples = [('Suginami Sans', False), ('Type freely', False), ('Type freely', True),
               ('Il1 O0 rn m vv w', False), ('u y g y', False), ('u y g y', True),
               ('AVATAR WA To Ta', False), ('$19.99 / x^2 / `code`', False)]
    image = Image.new('RGB', (1700, 1200), '#f4f2eb')
    draw = ImageDraw.Draw(image)
    draw.text((30, 20), 'Suginami Sans / Extended Bold / 0.105', fill='black')
    for index, (text, alternate) in enumerate(samples):
        mask = render_text(ROOT / (config['output_stem'] + '.otf'), text, 64, alternate)
        image.paste('black', (30, 65 + index * 140), mask)
        draw.text((30, 155 + index * 140), 'ss01' if alternate else 'default', fill='#555555')
    image.save(output / 'specimen.png')
    for ext in ['otf', 'ttf']:
        path = ROOT / (config['output_stem'] + '.' + ext)
        for size in [12, 16, 24, 48, 96]:
            for name, glyph in source.items():
                if name == 'space':
                    continue
                text = 'y' if name == 'y.alt' else chr(glyph['unicode'])
                mask = render_text(path, text, size, name == 'y.alt')
                records.append({'format': ext, 'glyph': name, 'size': size,
                                'holes': holes(mask), 'expected': expected[name]})
            for text, alternate in samples:
                render_text(path, text, size, alternate)
                clipping += 2  # Same glyph coverage in normal and inverted colors.
        for char, count in [('a', 1), ('s', 0), ('%', 2), ('@', 1)]:
            for size in [12, 13, 14, 15, 16]:
                for x, y in itertools.product([0, .25, .5, .75], repeat=2):
                    mask = render_text(path, char, size, phase_x=x, phase_y=y)
                    phases.append({'format': ext, 'glyph': char, 'size': size,
                                   'phase': [x, y], 'holes': holes(mask), 'expected': count})
    failures = [r for r in records + phases if r['holes'] != r['expected']]
    write_json('docs/RASTER_VALIDATION.json', {'result': 'PASS' if not failures else 'FAIL',
        'method': 'HarfBuzz + FreeType unhinted; enclosed 4-connected background at alpha < 128',
        'fonts': {ext: sha256(ROOT / (config['output_stem'] + '.' + ext)) for ext in ['otf', 'ttf']},
        'ordinary_cases': len(records), 'phase_cases': len(phases),
        'normal_inverted_layouts_without_clipping': clipping, 'failures': failures,
        'limits': 'Specified rasterizer/sizes/phases only; threshold-sensitive topology; installed apps untested.',
        'ordinary': records, 'phases': phases})
    rows = ''.join(f'<section><small>{size}px</small><div class="sample" style="font-size:{size}px">Il1 O0 rn m vv w / u y g y</div><div class="sample alt dark" style="font-size:{size}px">Il1 O0 rn m vv w / u y g y</div></section>' for size in [12,16,24,48,96])
    grid = ''.join(f'<span class="sample {"alt" if name == "y.alt" else ""}" title="{html.escape(name)}">{html.escape("y" if name == "y.alt" else chr(g["unicode"]))}</span>' for name,g in source.items() if name != 'space')
    page = '''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Suginami Sans — 文字見本</title>
<style>@font-face{font-family:SuginamiOTF;src:url('../fonts/SuginamiSans-ExtendedBold.otf');font-weight:700}@font-face{font-family:SuginamiTTF;src:url('../fonts/SuginamiSans-ExtendedBold.ttf');font-weight:700}:root{--face:SuginamiOTF}body{max-width:1400px;margin:32px auto;padding:0 20px;font-family:system-ui;background:#f4f2eb}section{margin:20px 0;padding:16px;background:white;overflow:auto}.sample{font-family:var(--face);font-weight:700;font-kerning:normal;font-synthesis:none;white-space:nowrap}.alt{font-feature-settings:"ss01" 1}.dark{background:#111;color:white;padding:8px}.grid{display:flex;flex-wrap:wrap;gap:20px}.grid span{font-size:48px}#editor{font-size:64px;overflow:auto;padding:24px 0}label{margin-right:20px}</style>
<h1>Suginami Sans / Extended Bold / 0.105</h1><p>印字可能ASCII95文字とen/em dash。代替yはss01で切り替えます。日本語・アクセント付き文字は未収録です。</p>
<label>形式 <select id="format"><option value="SuginamiOTF">OTF</option><option value="SuginamiTTF">TTF</option></select></label><label><input id="alternate" type="checkbox">代替y / ss01</label><label><input id="kern" type="checkbox" checked>カーニング</label><label>サイズ <input id="size" type="range" min="12" max="120" value="64"></label>
<div id="editor" class="sample" contenteditable="true" spellcheck="false">Type freely</div><div id="status" aria-live="polite">フォント読込中</div>
__ROWS__<h2>全字形</h2><div class="grid">__GRID__</div>
<script>const editor=document.getElementById('editor');document.getElementById('format').onchange=e=>document.documentElement.style.setProperty('--face',e.target.value);document.getElementById('alternate').onchange=e=>editor.classList.toggle('alt',e.target.checked);document.getElementById('kern').onchange=e=>editor.style.fontKerning=e.target.checked?'normal':'none';document.getElementById('size').oninput=e=>editor.style.fontSize=e.target.value+'px';Promise.all(['SuginamiOTF','SuginamiTTF'].map(f=>document.fonts.load('700 64px '+f,'Type freely'))).then(faces=>{document.getElementById('status').textContent=faces.every(f=>f.length)?'OTF / TTF 読込済み':'フォント読込失敗'}).catch(()=>document.getElementById('status').textContent='フォント読込失敗');</script></html>'''
    (output / 'index.html').write_text(page.replace('__ROWS__', rows).replace('__GRID__', grid), encoding='utf-8', newline='\n')
    print(f'Raster: {len(records)} ordinary + {len(phases)} phase checks; {len(failures)} failures')
    if failures:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
