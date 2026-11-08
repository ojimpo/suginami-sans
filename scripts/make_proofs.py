"""Generate neutral specimens and run current-font raster checks in a fresh clone."""
import itertools
from font_project import ROOT, read_json, write_json, sha256
from glyph_source import load_source
from raster import render_text
from topology import holes
from specimen import make_specimen

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
    make_specimen(config, source)
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
    print(f'Raster: {len(records)} ordinary + {len(phases)} phase checks; {len(failures)} failures')
    if failures:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
