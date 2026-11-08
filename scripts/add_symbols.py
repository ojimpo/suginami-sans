"""Append authored symbols to the editable UFO; preserve all existing glyphs."""
import argparse
from types import SimpleNamespace
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib import UFOReader, UFOWriter

from font_project import ROOT, read_json, read_ufo, sha256
from make_font_source import normalized


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ufo')
    args = parser.parse_args()
    config, info, order, glyphs, _, _, _ = read_ufo(ROOT / args.ufo if args.ufo else None)
    source = read_json('source/additional-glyphs.json')['glyphs']
    ufo = ROOT / (args.ufo or config['ufo_path'])
    scale = config['design_scale_numerator'] / config['design_scale_denominator']
    missing = {}
    for name, g in source.items():
        if name in glyphs:
            assert glyphs[name][0].unicodes == [g['unicode']], name
            continue
        record = RecordingPen()
        normalized(g).draw(TransformPen(record, Transform(scale, 0, 0, -scale,
                           g['font_origin_shift_x'] * scale, config['svg_baseline'] * scale)))
        glyph = SimpleNamespace(width=round(g['advance'] * scale), unicodes=[g['unicode']],
                                lib={'org.suginamisans.sourceRole': g['reference_role']})
        missing[name] = (glyph, record)
        order.append(name)
    reader = UFOReader(ufo)
    lib = reader.readLib()
    reader.close()
    info.versionMinor = config['version_minor']
    info.note = config['metrics_status']
    lib['public.glyphOrder'] = order
    lib['org.suginamisans.metricsStatus'] = config['metrics_status']
    lib['org.suginamisans.additionalSourceSHA256'] = sha256(ROOT / 'source/additional-glyphs.json')
    with UFOWriter(ufo, formatVersion=3) as writer:
        writer.writeInfo(info)
        writer.writeLib(lib)
        glyphset = writer.getGlyphSet()
        for name, (glyph, pen) in missing.items():
            glyphset.writeGlyph(name, glyph, lambda pp, p=pen: p.replay(SegmentToPointPen(pp)))
        glyphset.writeContents()
    print(f'Added {len(missing)} symbols; existing glyphs preserved; total {len(order)} glyphs.')


if __name__ == '__main__':
    main()
