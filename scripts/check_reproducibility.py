"""Rebuild both formats from initial JSON in an isolated tree without Git history."""
import shutil
import subprocess
import sys
import tempfile
from font_project import ROOT, read_ufo, sha256, write_json

def main():
    (ROOT / 'work').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='reproduce-', dir=ROOT / 'work') as directory:
        from pathlib import Path
        target = Path(directory)
        shutil.copytree(ROOT / 'scripts', target / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copyfile(ROOT / 'OFL.txt', target / 'OFL.txt')
        shutil.copytree(ROOT / 'source', target / 'source', ignore=shutil.ignore_patterns('*.ufo'))
        (target / 'docs').mkdir()
        for name in ['make_font_source.py', 'apply_spacing.py', 'apply_small_size.py',
                     'add_symbols.py', 'apply_release_size.py', 'build_fonts.py']:
            subprocess.run([sys.executable, str(target / 'scripts' / name)], cwd=target, check=True)
        _, _, order, original, features, kerning, groups = read_ufo()
        _, _, new_order, rebuilt, new_features, new_kerning, new_groups = read_ufo(target / 'source/SuginamiSans-ExtendedBold.ufo')
        assert order == new_order and features == new_features
        assert kerning == new_kerning and groups == new_groups
        for name in order:
            a, b = original[name], rebuilt[name]
            assert a[0].width == b[0].width and getattr(a[0], 'unicodes', []) == getattr(b[0], 'unicodes', []), name
            assert a[1].value == b[1].value, name
        hashes = {}
        for ext in ['otf', 'ttf']:
            name = f'fonts/SuginamiSans-ExtendedBold.{ext}'
            assert (ROOT / name).read_bytes() == (target / name).read_bytes(), name
            hashes[ext] = sha256(ROOT / name)
    write_json('docs/REPRODUCIBILITY.json', {'result': 'PASS', 'glyphs': len(order),
        'checks': ['initial JSON to UFO outlines and advances exact', 'Unicode, order, features, groups and kerning exact',
                   'OTF and TTF byte-identical to checked-in files', 'no Git history required'],
        'fonts': hashes})
    print('PASS: initial JSON -> UFO -> byte-identical OTF/TTF in isolated tree')

if __name__ == '__main__':
    main()
