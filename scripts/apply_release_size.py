"""Apply the explicit a/s/%/@ release optical corrections; keep imported originals."""
import argparse
from fontTools.misc.transform import Transform
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib import UFOReader, UFOWriter
from font_project import ROOT, read_json, read_ufo, recording_bounds, sha256, write_json
from small_size_project import corrected_at, corrected_percent, corrected_open_letter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ufo')
    parser.add_argument('--report', default='docs/RELEASE_SIZE_ADJUSTMENTS.json')
    args = parser.parse_args()
    config, info, _, glyphs, _, _, _ = read_ufo(ROOT / args.ufo if args.ufo else None)
    plan = read_json('source/release-size-plan.json')
    assert sha256(ROOT / 'source/glyphs.json') == plan['source_sha256']
    source = read_json('source/glyphs.json')['glyphs']
    scale = config['design_scale_numerator'] / config['design_scale_denominator']
    replacements, changes, designs = {}, {}, {}
    for name, settings in plan['glyphs'].items():
        function = {'uni0040': corrected_at, 'uni0025': corrected_percent}.get(name, corrected_open_letter)
        path = function(source[name], settings)
        glyph, current = glyphs[name]
        bounds = recording_bounds(current)
        left, right = bounds[0], glyph.width - bounds[2]
        record = RecordingPen()
        path.draw(TransformPen(record, Transform(scale, 0, 0, -scale,
                  left - path.bounds[0] * scale, config['svg_baseline'] * scale)))
        glyph.width = round((path.bounds[2] - path.bounds[0]) * scale + left + right)
        glyph.lib['org.suginamisans.opticalCorrection'] = '0.105 release-size-plan.json'
        replacements[name] = glyph, record
        pen = SVGPathPen(None); path.draw(pen)
        designs[name] = {'d': pen.getCommands(), 'bounds': list(path.bounds)}
        changes[name] = {'advance': glyph.width, 'ufo_bounds': recording_bounds(record), 'plan': settings}
    ufo = ROOT / (args.ufo or config['ufo_path'])
    reader = UFOReader(ufo); lib = reader.readLib(); reader.close()
    info.versionMinor = config['version_minor']; info.note = config['metrics_status']
    lib['org.suginamisans.metricsStatus'] = config['metrics_status']
    lib['org.suginamisans.releaseSizePlanSHA256'] = sha256(ROOT / 'source/release-size-plan.json')
    with UFOWriter(ufo, formatVersion=3) as writer:
        writer.writeInfo(info); writer.writeLib(lib)
        glyphset = writer.getGlyphSet()
        for name, (glyph, pen) in replacements.items():
            glyphset.writeGlyph(name, glyph, lambda pp, p=pen: p.replay(SegmentToPointPen(pp)))
        glyphset.writeContents()
    write_json(args.report, {'version': '0.105', 'source_sha256': plan['source_sha256'],
                            'changes': changes, 'expected_svg_paths': designs,
                            'scope': 'Only a, s, % and @. Imported JSON and original logo remain immutable.'})
    print('Applied release-size corrections: ' + ', '.join(f'{n} {g.width}' for n, (g, _) in replacements.items()))


if __name__ == '__main__':
    main()
