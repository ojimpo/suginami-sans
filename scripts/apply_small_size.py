"""Explicitly apply the %/@ optical plan, preserving all other editable glyphs."""
import argparse
from fontTools.misc.transform import Transform
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib import UFOReader, UFOWriter

from font_project import ROOT, read_json, read_ufo, recording_bounds, sha256, write_json
from small_size_project import corrected_percent, corrected_at


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ufo')
    parser.add_argument('--report', default='docs/SMALL_SIZE_ADJUSTMENTS.json')
    args = parser.parse_args()
    config, info, _, glyphs, _, _, _ = read_ufo(ROOT / args.ufo if args.ufo else None)
    plan = read_json('source/small-size-plan.json')
    assert sha256(ROOT / 'source/glyphs.json') == plan['source_sha256'], 'Canonical source changed; re-audit region mapping'
    source = read_json('source/glyphs.json')['glyphs']
    scale = config['design_scale_numerator'] / config['design_scale_denominator']
    ufo = ROOT / (args.ufo or config['ufo_path'])
    changes, expected_paths, replacements = {}, {}, {}
    for name, function in [('uni0025', corrected_percent), ('uni0040', corrected_at)]:
        original = source[name]
        path = function(original, plan['glyphs'][name])
        new_source_bounds = list(path.bounds)
        # Preserve the 0.102 sidebearings; let only these two advances grow.
        left = original['left_sidebearing'] * scale
        old_width = round(original['advance'] * scale)
        old_ink_width = (original['bounds'][2] - original['bounds'][0]) * scale
        right = old_width - left - old_ink_width
        record = RecordingPen()
        path.draw(TransformPen(record, Transform(scale, 0, 0, -scale,
                  left - path.bounds[0] * scale, config['svg_baseline'] * scale)))
        glyph = glyphs[name][0]
        glyph.width = round((path.bounds[2] - path.bounds[0]) * scale + left + right)
        glyph.lib['org.suginamisans.opticalCorrection'] = '0.103 small-size-plan.json'
        replacements[name] = (glyph, record)
        pen = SVGPathPen(None)
        path.draw(pen)
        expected_paths[name] = {'d': pen.getCommands(), 'bounds': new_source_bounds}
        changes[name] = {'baseline_advance': old_width, 'advance': glyph.width,
                         'lsb_preserved': left, 'ufo_bounds': recording_bounds(record),
                         'plan': plan['glyphs'][name]}
    reader = UFOReader(ufo)
    lib = reader.readLib()
    reader.close()
    info.versionMinor = config['version_minor']
    info.note = config['metrics_status']
    lib['org.suginamisans.metricsStatus'] = config['metrics_status']
    lib['org.suginamisans.smallSizePlanVersion'] = plan['version_minor']
    with UFOWriter(ufo, formatVersion=3) as writer:
        writer.writeInfo(info)
        writer.writeLib(lib)
        glyphset = writer.getGlyphSet()
        for name, (glyph, pen) in replacements.items():
            glyphset.writeGlyph(name, glyph, lambda pp, p=pen: p.replay(SegmentToPointPen(pp)))
        glyphset.writeContents()
    write_json(args.report, {'version': '0.103', 'source_sha256': plan['source_sha256'],
               'changes': changes, 'expected_svg_paths': expected_paths,
               'scope': 'Only % and @. Canonical JSON and official logo unchanged.'})
    print('Applied small-size optical corrections: ' + ', '.join(f'{n} {r["advance"]}' for n, r in changes.items()))


if __name__ == '__main__':
    main()
