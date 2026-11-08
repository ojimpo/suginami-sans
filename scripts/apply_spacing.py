"""Apply the explicit spacing plan to a UFO, translating ink without reshaping it."""
import argparse
import math

from fontTools.misc.transform import Transform
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib import UFOReader, UFOWriter

from font_project import ROOT, read_json, read_ufo, recording_bounds, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ufo', help='Alternate UFO for a reproducibility check')
    parser.add_argument('--report', default='docs/SPACING_ADJUSTMENTS.json')
    args = parser.parse_args()
    config, info, order, glyphs, _, kerning, groups = read_ufo(ROOT / args.ufo if args.ufo else None)
    ufo = ROOT / (args.ufo or config['ufo_path'])
    plan = read_json('source/spacing-plan.json')
    reader = UFOReader(ufo)
    lib = reader.readLib()
    reader.close()
    changes = {}
    for name, target in plan['bearings'].items():
        glyph, original = glyphs[name]
        bounds = recording_bounds(original)
        left, right = target
        shift = left - bounds[0]
        moved = RecordingPen()
        original.replay(TransformPen(moved, Transform().translate(shift, 0)))
        for (op, points), (new_op, new_points) in zip(original.value, moved.value):
            assert op == new_op
            for a, b in zip(points, new_points):
                assert math.isclose(a[0] + shift, b[0], abs_tol=1e-7) and a[1] == b[1]
        before_advance = glyph.width
        glyph.width = round(bounds[2] - bounds[0] + left + right)
        glyphs[name] = (glyph, moved)
        changes[name] = {'before_advance': before_advance, 'after_advance': glyph.width,
                         'target_lsb': left, 'target_rsb': right, 'shift_x': shift,
                         'ink_reshaped': False}
    glyphs['space'][0].width = plan['space_advance']
    groups.update(plan['groups'])
    # This explicit command treats the plan as the kerning source of truth.
    # Normal build_fonts.py still respects hand-edited UFO kerning unchanged.
    kerning = {}
    for pair, value in plan['kerning'].items():
        left, right = pair.split()
        for side in [left, right]:
            assert side in glyphs or side in groups, side
        kerning[left, right] = value
    for members in groups.values():
        assert all(name in glyphs for name in members)
    info.versionMinor = config['version_minor']
    info.note = config['metrics_status']
    lib['org.suginamisans.metricsStatus'] = config['metrics_status']
    lib['org.suginamisans.spacingPlanVersion'] = plan['version_minor']
    with UFOWriter(ufo, formatVersion=3) as writer:
        writer.writeInfo(info)
        writer.writeLib(lib)
        writer.writeGroups(groups)
        writer.writeKerning(kerning)
        glyphset = writer.getGlyphSet()
        for name, (glyph, pen) in glyphs.items():
            glyphset.writeGlyph(name, glyph, lambda pp, p=pen: p.replay(SegmentToPointPen(pp)))
        glyphset.writeContents()
    write_json(args.report, {'version': '0.102', 'bearing_glyphs': len(changes),
                            'kerning_rules': len(kerning), 'space_advance': plan['space_advance'],
                            'geometry_policy': 'translation only; canonical JSON and official logo untouched',
                            'changes': changes})
    print(f'Applied spacing: {len(changes)} bearings, {len(kerning)} kerning rules; space {plan["space_advance"]}')


if __name__ == '__main__':
    main()
