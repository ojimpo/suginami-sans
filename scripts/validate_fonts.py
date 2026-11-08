"""Validate static binaries, editable source, shaping, extents and winding."""
import hashlib
import math
import subprocess

import pathops
import uharfbuzz as hb
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont

from font_project import ROOT, read_json, read_ufo, sha256, write_json
from glyph_source import load_source


def shape(font_path, text, ss01=False):
    font = hb.Font(hb.Face(font_path.read_bytes()))
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer, {'ss01': int(ss01)})
    return [g.codepoint for g in buffer.glyph_infos]


def check_path(path, clockwise):
    """Same area under evenodd/nonzero; simplifying again must not remove ink."""
    evenodd = pathops.Path(path)
    evenodd.fillType = pathops.FillType.EVEN_ODD
    winding = pathops.Path(path)
    winding.fillType = pathops.FillType.WINDING
    difference = pathops.op(evenodd, winding, pathops.PathOp.XOR)
    if abs(difference.area) > 0.01:
        raise AssertionError('evenodd and nonzero produce different ink')
    simplified = pathops.simplify(winding, clockwise=clockwise)
    delta = abs(abs(path.area) - abs(simplified.area))
    if delta > max(0.05, abs(path.area) * 0.00001):
        raise AssertionError(f'Overlap or self-intersection changes signed ink area: {delta}')
    areas = []
    for contour in path.contours:
        pen = AreaPen()
        contour.draw(pen)
        if abs(pen.value) < 0.000001:
            raise AssertionError('Zero-area contour')
        areas.append(pen.value)
    if areas:
        largest = max(areas, key=abs)
        if (largest < 0) != clockwise:
            raise AssertionError('Unexpected outer contour direction')
    return {'contours': len(areas), 'signed_area': path.area,
            'winding_xor_area': difference.area, 'simplification_area_delta': delta}


def main():
    config, info, order, glyphs, _, kerning, _ = read_ufo()
    source = load_source()['glyphs']
    expected_cmap = {g['unicode']: name for name, g in source.items() if g['unicode'] is not None}
    expected_order = {'.notdef', *source}
    assert set(order) == expected_order and order[0] == '.notdef'
    assert len(order) == len(source) + 1
    assert all(cp in expected_cmap for cp in range(32, 127))
    assert glyphs['y'][0].unicodes == [0x79]
    assert not getattr(glyphs['y.alt'][0], 'unicodes', [])
    assert not glyphs['space'][1].value
    assert glyphs['.notdef'][1].value
    ufo_checks = {}
    for name, (_, recording) in glyphs.items():
        path = pathops.Path()
        recording.replay(path.getPen())
        ufo_checks[name] = check_path(path, clockwise=False)
    # A fresh clone must validate without historical commits or external artwork.
    immutable_checks = read_json('source/input-checksums.json')
    for name, expected in immutable_checks.items():
        assert sha256(ROOT / name) == expected, name
    reports = {}
    for ext in ['otf', 'ttf']:
        path = ROOT / (config['output_stem'] + '.' + ext)
        font = TTFont(path, lazy=False, checkChecksums=2)
        # Parse and compile every table, exercising complete binary round-trip.
        for tag in font.keys():
            if tag != 'GlyphOrder':
                font[tag].compile(font)
        assert font.getBestCmap() == expected_cmap
        assert font.getGlyphOrder() == order
        assert font['name'].getDebugName(16) == 'Suginami Sans'
        assert font['name'].getDebugName(17) == 'Extended Bold'
        assert font['OS/2'].usWeightClass == 700 and font['OS/2'].usWidthClass == 7
        assert font['OS/2'].fsSelection & (1 << 7)
        assert 'fvar' not in font
        gids = {name: font.getGlyphID(name) for name in ['y', 'y.alt', '.notdef']}
        assert shape(path, 'y') == [gids['y']]
        assert shape(path, 'y', True) == [gids['y.alt']]
        for text in ['type', 'Il1 O0 rn m vv w u y g y', 'Suginami Sans', 'Kouki Ojima', 'Suginami P1', '$19.99', 'x^2', '`code`']:
            assert 0 not in shape(path, text), text
        glyphset = font.getGlyphSet()
        checks = {}
        for name in order:
            recording = RecordingPen()
            glyphset[name].draw(recording)
            assert not any(op == 'endPath' for op, _ in recording.value), name
            for _, points in recording.value:
                for point in points:
                    if point is not None:
                        assert all(math.isfinite(c) for c in point), name
            outline = pathops.Path()
            recording.replay(outline.getPen())
            checks[name] = check_path(outline, clockwise=ext == 'ttf')
            if recording.value:
                x0, y0, x1, y1 = outline.bounds
                assert y0 >= info.descender and y1 <= info.ascender, name
                assert y0 >= -font['OS/2'].usWinDescent - 0.01, name
                assert y1 <= font['OS/2'].usWinAscent + 0.01, name
                advance, _ = font['hmtx'][name]
                assert x0 >= 0 and x1 <= advance, (name, x0, x1, advance)
            assert font['hmtx'][name][0] == round(glyphs[name][0].width)
        if ext == 'ttf':
            assert all(not getattr(g, 'program', None) or not g.program.getBytecode()
                       for g in font['glyf'].glyphs.values())
        reports[ext] = {'sha256': sha256(path), 'bytes': path.stat().st_size,
                        'glyph_count': len(order), 'cmap_count': len(expected_cmap),
                        'default_y_gid': gids['y'], 'ss01_y_gid': gids['y.alt'],
                        'line_extents': [font['head'].yMin, font['head'].yMax],
                        'tables': list(font.keys()), 'glyph_checks': checks}
        font.close()
    missing_ascii = [chr(cp) for cp in range(32, 127) if cp not in expected_cmap]
    write_json('docs/STATIC_VALIDATION.json', {
        'result': 'PASS', 'ufo_glyph_count': len(order), 'ufo_checks': ufo_checks,
        'immutable_input_sha256': immutable_checks, 'fonts': reports,
        'missing_printable_ascii': missing_ascii, 'kerning_pairs': len(kerning),
        'passed': ['UFO v3 validation', 'all binary table round-trips', 'Unicode exact coverage',
                   'HarfBuzz default y and ss01', 'closed finite outlines',
                   'nonzero/evenodd area equivalence', 'outer contour direction',
                   'signed ink area after simplification', 'no metric clipping', 'input checksums match'],
        'limits': ['not an independent exact curve self-intersection proof',
                   'no hinting; optical spacing is an initial pass', 'no variable font',
                   'Windows app evaluation pending; browser and raster checks recorded separately'],
    })
    print(f'PASS: UFO + OTF/TTF, {len(order)} glyphs, printable ASCII, ss01, winding, extents, input checksums. Missing ASCII: {missing_ascii}')


if __name__ == '__main__':
    main()
