"""Package a verified allow-list of font files and standalone documentation."""
import hashlib
import zipfile
from font_project import ROOT, read_json, sha256, write_json

def main():
    config = read_json('source/font-config.json')
    version = f'{config["version_major"]}.{config["version_minor"]:03d}'
    release_notes = f'docs/RELEASE_{config["version_major"]}{config["version_minor"]:03d}.md'
    static = read_json('docs/STATIC_VALIDATION.json')
    raster = read_json('docs/RASTER_VALIDATION.json')
    reproduced = read_json('docs/REPRODUCIBILITY.json')
    browser = read_json('docs/BROWSER_SPECIMEN_VALIDATION.json')
    specimen = read_json('docs/SPECIMEN_BUILD.json')
    licensing = read_json('docs/OFL_VALIDATION.json')
    assert static['result'] == raster['result'] == reproduced['result'] == browser['result'] == 'PASS'
    assert licensing['result'] == 'PASS'
    assert licensing['license_file_sha256'] == sha256(ROOT / config['license_file'])
    for name, expected in browser['source_files'].items():
        assert sha256(ROOT / name) == expected, f'Stale browser verification: {name}'
    for name, expected in specimen['files'].items():
        assert sha256(ROOT / 'proofs' / name) == expected, f'Stale specimen: {name}'
    files = {f'SuginamiSans-ExtendedBold.{ext}': ROOT / f'fonts/SuginamiSans-ExtendedBold.{ext}' for ext in ['otf', 'ttf']}
    for ext in ['otf', 'ttf']:
        actual = sha256(ROOT / f'fonts/SuginamiSans-ExtendedBold.{ext}')
        assert actual == static['fonts'][ext]['sha256'] == raster['fonts'][ext] == reproduced['fonts'][ext]
        assert actual == licensing['fonts'][ext]['font_sha256']
    files.update({'README.md': ROOT / 'docs/USAGE.md', 'PROVENANCE.md': ROOT / 'docs/PROVENANCE.md',
                  'VALIDATION.md': ROOT / 'docs/VALIDATION.md', 'RELEASE_NOTES.md': ROOT / release_notes,
                  'OFL.txt': ROOT / 'OFL.txt',
                  'specimen.png': ROOT / 'proofs/specimen.png', 'specimen/index.html': ROOT / 'proofs/index.html',
                  'specimen/specimen.css': ROOT / 'proofs/specimen.css', 'specimen/specimen.js': ROOT / 'proofs/specimen.js'})
    payload = {name: path.read_bytes() for name, path in files.items()}
    payload['specimen/specimen.css'] = payload['specimen/specimen.css'].replace(b'../fonts/', b'../')
    payload['specimen/index.html'] = payload['specimen/index.html'].replace(b'href="specimen.png"', b'href="../specimen.png"')
    payload['SHA256SUMS.txt'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in sorted(payload.items())).encode('ascii')
    output = ROOT / 'releases' / version
    output.mkdir(parents=True, exist_ok=True)
    directory_name = f'SuginamiSans-ExtendedBold-{version}'
    archive_path = output / (directory_name + '.zip')
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo(directory_name + '/' + name, date_time=(2026, 11, 8, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        for name, data in payload.items():
            assert archive.read(directory_name + '/' + name) == data
    outputs = [archive_path]
    for ext in ['otf', 'ttf']:
        path = output / f'SuginamiSans-ExtendedBold.{ext}'
        path.write_bytes(files[path.name].read_bytes())
        outputs.append(path)
    image = output / 'specimen.png'
    image.write_bytes(files['specimen.png'].read_bytes())
    outputs.append(image)
    license_file = output / 'OFL.txt'
    license_file.write_bytes((ROOT / 'OFL.txt').read_bytes())
    outputs.append(license_file)
    (output / 'SHA256SUMS.txt').write_text(''.join(sha256(path) + '  ' + path.name + '\n' for path in outputs), encoding='ascii', newline='\n')
    write_json('docs/RELEASE_PACKAGE.json', {'result': 'PASS', 'version': version, 'members': sorted(payload),
        'assets': {path.name: sha256(path) for path in [*outputs, output / 'SHA256SUMS.txt']}})
    print(archive_path)

if __name__ == '__main__':
    main()
