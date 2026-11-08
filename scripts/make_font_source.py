"""Explicitly derive a new cubic UFO from JSON; never overwrite an existing UFO."""
from types import SimpleNamespace
import argparse
import math

import pathops
from fontTools.misc.transform import Transform
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from fontTools.ufoLib import UFOWriter

from font_project import ROOT, read_json, recording_bounds, sha256, write_json
from glyph_source import load_source


def normalized(glyph):
    """Simplify each painted SVG path by its own fill rule, then union paints."""
    combined = pathops.Path()
    for item in glyph['paths']:
        path = pathops.Path()
        path.fillType = (pathops.FillType.EVEN_ODD if item['fill_rule'] == 'evenodd'
                         else pathops.FillType.WINDING)
        parse_path(item['d'], path.getPen())
        # SVG Y-down becomes Y-up below: reverse the source convention here.
        clean = pathops.simplify(path, fix_winding=True, clockwise=True)
        combined = pathops.op(combined, clean, pathops.PathOp.UNION, clockwise=True)
    return combined


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='New UFO path, relative to the project root')
    args = parser.parse_args()
    config = read_json('source/font-config.json')
    source = load_source()
    output = ROOT / (args.output or config['ufo_path'])
    if output.exists():
        raise SystemExit(f'Refusing to overwrite editable source: {output}')
    scale = config['design_scale_numerator'] / config['design_scale_denominator']
    glyphs = {}
    audit = {}
    paths = {}
    # CCW outer / CW inner in Y-up space, consistent with cubic PostScript UFO.
    notdef = RecordingPen()
    for points in [[(50, 0), (550, 0), (550, 700), (50, 700)],
                   [(150, 100), (150, 600), (450, 600), (450, 100)]]:
        notdef.moveTo(points[0])
        for pt in points[1:]:
            notdef.lineTo(pt)
        notdef.closePath()
    glyphs['.notdef'] = (SimpleNamespace(width=600, unicodes=[], lib={}), notdef)
    for name, glyph in source['glyphs'].items():
        clean = normalized(glyph)
        pen = RecordingPen()
        transform = Transform(scale, 0, 0, -scale,
                              glyph['font_origin_shift_x'] * scale,
                              config['svg_baseline'] * scale)
        clean.draw(TransformPen(pen, transform))
        # Floating source coordinates retained; font advances are integer units.
        record = SimpleNamespace(width=round(glyph['advance'] * scale),
                                 unicodes=[] if glyph['unicode'] is None else [glyph['unicode']],
                                 lib={'org.suginamisans.sourceRole': glyph['reference_role']})
        glyphs[name] = (record, pen)
        svgpen = SVGPathPen(None)
        clean.draw(svgpen)
        paths[name] = svgpen.getCommands()
        audit[name] = {
            'source_paths': len(glyph['paths']),
            'normalized_contours': len(list(clean.contours)),
            'source_fill_rules': sorted({p['fill_rule'] for p in glyph['paths']}),
            'ufo_bounds': recording_bounds(pen),
            'advance': record.width,
            'contour_absolute_areas_svg': [c.area for c in clean.contours],
        }
    bounds = [recording_bounds(pen) for _, pen in glyphs.values()]
    top = max(b[3] for b in bounds if b)
    bottom = min(b[1] for b in bounds if b)
    if top > config['ascender'] or bottom < config['descender']:
        raise ValueError('Configured line metrics clip outline extents')
    info = SimpleNamespace(
        copyright=config['copyright'],
        openTypeNameLicense=(ROOT / config['license_file']).read_text(encoding='utf-8'),
        openTypeNameLicenseURL=config['license_url'],
        familyName=config['family'], styleName=config['style'],
        styleMapFamilyName='Suginami Sans Extended', styleMapStyleName='bold',
        unitsPerEm=config['units_per_em'], capHeight=config['cap_height'],
        xHeight=config['x_height'], ascender=config['ascender'], descender=config['descender'],
        versionMajor=config['version_major'], versionMinor=config['version_minor'],
        openTypeOS2WeightClass=config['weight_class'], openTypeOS2WidthClass=config['width_class'],
        openTypeHheaAscender=config['ascender'], openTypeHheaDescender=config['descender'],
        openTypeHheaLineGap=0, openTypeOS2TypoAscender=config['ascender'],
        openTypeOS2TypoDescender=config['descender'], openTypeOS2TypoLineGap=0,
        openTypeOS2WinAscent=math.ceil(top), openTypeOS2WinDescent=math.ceil(-bottom),
        openTypeOS2Selection=[7], openTypeOS2Type=[],
        postscriptFontName='SuginamiSans-ExtendedBold',
        note=config['metrics_status'],
    )
    with UFOWriter(output, formatVersion=3) as writer:
        writer.writeInfo(info)
        writer.writeLib({'public.glyphOrder': list(glyphs),
                         'org.suginamisans.metricsStatus': config['metrics_status'],
                         'org.suginamisans.sourceSHA256': sha256(ROOT / 'source/glyphs.json')})
        writer.writeGroups({})
        writer.writeKerning({})
        writer.writeFeatures('feature ss01 {\n  featureNames { name "Logo y"; };\n  sub y by y.alt;\n} ss01;\n')
        glyphset = writer.getGlyphSet()
        for name, (glyph, pen) in glyphs.items():
            glyphset.writeGlyph(name, glyph, lambda pointpen, p=pen: p.replay(SegmentToPointPen(pointpen)))
        glyphset.writeContents()
        writer.writeLayerContents()
    write_json('docs/OUTLINE_NORMALIZATION.json', {
        'tool': 'skia-pathops ' + pathops.__version__,
        'method': 'per-path SVG fill simplify, union painted paths, Y-up transform; CCW cubic outer',
        'source_sha256': sha256(ROOT / 'source/glyphs.json'),
        'additional_source_sha256': sha256(ROOT / 'source/additional-glyphs.json'),
        'font_extents': [bottom, top], 'normalized_svg_paths': paths, 'glyphs': audit,
    })
    print(f'Created editable UFO: {output} ({len(glyphs)} glyphs); extents {bottom:.3f}..{top:.3f}')


if __name__ == '__main__':
    main()
