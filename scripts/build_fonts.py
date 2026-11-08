"""Build deterministic static OTF/TTF from the editable UFO, without regenerating it."""
from datetime import datetime
import re
import pathops

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.timeTools import timestampSinceEpoch
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

from font_project import ROOT, read_ufo, recording_bounds, sha256, write_json


def kerning_features(kerning, groups):
    if not kerning:
        return ''
    declarations = []
    aliases = {}
    for index, (name, members) in enumerate(sorted(groups.items())):
        if name.startswith('public.kern'):
            aliases[name] = f'@ufoKern{index}'
            declarations.append(f'{aliases[name]} = [{" ".join(members)}];')
    pairs = [f'  pos {aliases.get(a, a)} {aliases.get(b, b)} {round(value)};'
             for (a, b), value in sorted(kerning.items())]
    return '\n'.join(declarations + ['feature kern {'] + pairs + ['} kern;'])


def main():
    config, info, order, glyphs, features, kerning, groups = read_ufo()
    if kerning and re.search(r'feature\s+kern\s*\{', features):
        raise ValueError('Use either UFO kerning.plist or an explicit kern feature, not both')
    features += '\n' + kerning_features(kerning, groups)
    cmap = {cp: name for name, (g, _) in glyphs.items() for cp in getattr(g, 'unicodes', [])}
    if len(cmap) != sum(len(getattr(g, 'unicodes', [])) for g, _ in glyphs.values()):
        raise ValueError('Duplicate UFO Unicode assignments')
    timestamp = timestampSinceEpoch(datetime.fromisoformat(config['timestamp_utc']).timestamp())
    outputs = {}
    degenerate_removed = []
    for is_ttf in [False, True]:
        fb = FontBuilder(info.unitsPerEm, isTTF=is_ttf)
        fb.setupGlyphOrder(order)
        fb.setupCharacterMap(cmap)
        if is_ttf:
            outlines = {}
            for name, (_, recording) in glyphs.items():
                pen = TTGlyphPen(None)
                recording.replay(Cu2QuPen(pen, config['cu2qu_max_error'], reverse_direction=True))
                glyph = pen.glyph()
                # Integer rounding can collapse a sub-unit source sliver to a
                # zero-area contour. Remove only collapsed ink, keep UFO/OTF intact.
                path = pathops.Path()
                glyph.draw(path.getPen(), None)
                contours = list(path.contours)
                kept = [contour for contour in contours if contour.area > 0]
                if len(kept) != len(contours):
                    clean_pen = TTGlyphPen(None)
                    for contour in kept:
                        contour.draw(clean_pen)
                    glyph = clean_pen.glyph()
                    degenerate_removed.append({'glyph': name, 'contours': len(contours) - len(kept)})
                outlines[name] = glyph
            fb.setupGlyf(outlines)
        else:
            charstrings = {}
            for name, (glyph, recording) in glyphs.items():
                pen = T2CharStringPen(round(glyph.width), None, roundTolerance=0)
                recording.replay(pen)
                charstrings[name] = pen.getCharString()
            fb.setupCFF(info.postscriptFontName, {
                'FullName': info.familyName + ' ' + info.styleName,
                'FamilyName': info.familyName, 'Weight': 'Bold',
                'version': f'{info.versionMajor}.{info.versionMinor:03d}',
            }, charstrings, {})
        metrics = {}
        for name, (glyph, recording) in glyphs.items():
            bounds = recording_bounds(recording)
            if is_ttf:
                ttg = outlines[name]
                ttg.recalcBounds(outlines)
                lsb = ttg.xMin if ttg.numberOfContours else 0
            else:
                lsb = round(bounds[0]) if bounds else 0
            metrics[name] = (round(glyph.width), lsb)
        fb.setupHorizontalMetrics(metrics)
        fb.setupHorizontalHeader(ascent=info.ascender, descent=info.descender,
                                 lineGap=info.openTypeHheaLineGap)
        version = f'{info.versionMajor}.{info.versionMinor:03d}'
        fb.setupNameTable({
            'familyName': info.styleMapFamilyName, 'styleName': 'Bold',
            'typographicFamily': info.familyName, 'typographicSubfamily': info.styleName,
            'fullName': info.familyName + ' ' + info.styleName,
            'psName': info.postscriptFontName,
            'uniqueFontIdentifier': f'SuginamiSans-{version}-ExtendedBold',
            'version': f'Version {version}' + ('' if config.get('release_status') == 'static' else '; prototype'),
            'description': ('Static Extended Bold. Printable ASCII; ss01 selects Logo y. Unhinted. Distribution license undecided.'
                            if config.get('release_status') == 'static' else
                            'Static prototype. Metrics and kerning are provisional. Distribution license undecided.'),
        })
        fb.setupOS2(version=4, sTypoAscender=info.ascender, sTypoDescender=info.descender,
                    sTypoLineGap=0, usWinAscent=info.openTypeOS2WinAscent,
                    usWinDescent=info.openTypeOS2WinDescent, sxHeight=info.xHeight,
                    sCapHeight=info.capHeight, usWeightClass=info.openTypeOS2WeightClass,
                    usWidthClass=info.openTypeOS2WidthClass, fsSelection=(1 << 5) | (1 << 7),
                    fsType=0)
        fb.setupPost(keepGlyphNames=True)
        fb.setupHead(created=timestamp, modified=timestamp, macStyle=1, fontRevision=float(version))
        addOpenTypeFeaturesFromString(fb.font, features)
        fb.font.recalcTimestamp = False
        output = ROOT / (config['output_stem'] + ('.ttf' if is_ttf else '.otf'))
        output.parent.mkdir(parents=True, exist_ok=True)
        fb.save(output)
        outputs[output.relative_to(ROOT).as_posix()] = sha256(output)
        print(f'Built {output.name}: {output.stat().st_size} bytes')
    write_json('docs/FONT_BUILD.json', {'version': version, 'outputs': outputs, 'glyphs': len(order),
               'encoded_characters': len(cmap), 'ufo': config['ufo_path'],
               'cu2qu_max_error_font_units': config['cu2qu_max_error'],
               'ttf_zero_area_contours_removed': degenerate_removed,
               'metrics_status': config['metrics_status']})


if __name__ == '__main__':
    main()
