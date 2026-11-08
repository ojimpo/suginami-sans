"""Apply configured version and OFL metadata to UFO info without touching glyphs."""
import plistlib
from font_project import ROOT, read_json


def main():
    config = read_json('source/font-config.json')
    ufo = ROOT / config['ufo_path']
    path = ufo / 'fontinfo.plist'
    info = plistlib.loads(path.read_bytes())
    info.update(versionMajor=config['version_major'], versionMinor=config['version_minor'],
                copyright=config['copyright'], note=config['metrics_status'],
                openTypeNameLicense=(ROOT / config['license_file']).read_text(encoding='utf-8'),
                openTypeNameLicenseURL=config['license_url'])
    path.write_bytes(plistlib.dumps(info, sort_keys=True))
    path = ufo / 'lib.plist'
    lib = plistlib.loads(path.read_bytes())
    lib['org.suginamisans.metricsStatus'] = config['metrics_status']
    path.write_bytes(plistlib.dumps(lib, sort_keys=True))
    print('Updated UFO version, copyright and OFL metadata; glyphs unchanged.')


if __name__ == '__main__':
    main()
