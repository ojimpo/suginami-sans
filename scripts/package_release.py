"""Package a verified allow-list of font files and standalone documentation."""
import hashlib
import zipfile
from font_project import ROOT, read_json, sha256, write_json

def main():
    static = read_json('docs/STATIC_VALIDATION.json')
    raster = read_json('docs/RASTER_VALIDATION.json')
    reproduced = read_json('docs/REPRODUCIBILITY.json')
    assert static['result'] == raster['result'] == reproduced['result'] == 'PASS'
    files = {f'SuginamiSans-ExtendedBold.{ext}': ROOT / f'fonts/SuginamiSans-ExtendedBold.{ext}' for ext in ['otf', 'ttf']}
    for ext in ['otf', 'ttf']:
        actual = sha256(ROOT / f'fonts/SuginamiSans-ExtendedBold.{ext}')
        assert actual == static['fonts'][ext]['sha256'] == raster['fonts'][ext] == reproduced['fonts'][ext]
    files.update({'README.md': ROOT / 'docs/USAGE.md', 'PROVENANCE.md': ROOT / 'docs/PROVENANCE.md',
                  'VALIDATION.md': ROOT / 'docs/VALIDATION.md', 'specimen.png': ROOT / 'proofs/specimen.png'})
    payload = {name: path.read_bytes() for name, path in files.items()}
    payload['SHA256SUMS.txt'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(payload.items())).encode('ascii')
    output = ROOT / 'releases/0.105'
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / 'SuginamiSans-ExtendedBold-0.105.zip'
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo('SuginamiSans-ExtendedBold-0.105/' + name, date_time=(2026, 11, 8, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        for name, data in payload.items():
            assert archive.read('SuginamiSans-ExtendedBold-0.105/' + name) == data
    outputs = [archive_path]
    for ext in ['otf', 'ttf']:
        path = output / f'SuginamiSans-ExtendedBold.{ext}'
        path.write_bytes(files[path.name].read_bytes())
        outputs.append(path)
    (output / 'SHA256SUMS.txt').write_text(''.join(sha256(path) + '  ' + path.name + '\n' for path in outputs), encoding='ascii', newline='\n')
    write_json('docs/RELEASE_PACKAGE.json', {'result': 'PASS', 'members': sorted(payload),
        'assets': {path.name: sha256(path) for path in [*outputs, output / 'SHA256SUMS.txt']}})
    print(archive_path)

if __name__ == '__main__':
    main()
