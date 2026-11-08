"""Check that the OFL release changes metadata, not font design, from 0.105."""
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from font_project import ROOT, read_json, sha256, write_json


def main():
    config = read_json('source/font-config.json')
    results = {}
    for ext in ['otf', 'ttf']:
        old_path = ROOT / f'releases/0.105/SuginamiSans-ExtendedBold.{ext}'
        new_path = ROOT / (config['output_stem'] + '.' + ext)
        with TTFont(old_path) as old, TTFont(new_path) as new:
            assert old.getBestCmap() == new.getBestCmap()
            assert old.getGlyphOrder() == new.getGlyphOrder()
            a, b = old.getGlyphSet(), new.getGlyphSet()
            for name in old.getGlyphOrder():
                before, after = RecordingPen(), RecordingPen()
                a[name].draw(before); b[name].draw(after)
                assert before.value == after.value, name
                assert old['hmtx'][name] == new['hmtx'][name], name
            tables = ['hhea', 'OS/2', 'GSUB', 'GPOS', 'hmtx', 'maxp', 'post']
            for tag in tables:
                assert old.getTableData(tag) == new.getTableData(tag), tag
            results[ext] = {'reference_sha256': sha256(old_path), 'font_sha256': sha256(new_path),
                            'glyphs_unchanged': len(old.getGlyphOrder()), 'tables_unchanged': tables,
                            'copyright': new['name'].getDebugName(0),
                            'license_url': new['name'].getDebugName(14)}
    write_json('docs/OFL_VALIDATION.json', {'result': 'PASS', 'version': '0.106',
        'reference_version': '0.105', 'scope': 'Version, copyright and license metadata only.',
        'license_file_sha256': sha256(ROOT / 'OFL.txt'), 'reserved_font_names': config['reserved_font_names'],
        'fonts': results})
    print('PASS: 99 glyphs, advances, layout and vertical metrics unchanged in both formats')


if __name__ == '__main__':
    main()
