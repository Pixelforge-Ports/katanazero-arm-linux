#!/usr/bin/env python3
"""Prepare the supplied Android YYC build with a guarded startup edit and the original native runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile


def digest(stream):
    result = hashlib.sha256()
    while True:
        block = stream.read(1024 * 1024)
        if not block:
            return result.hexdigest()
        result.update(block)


def verify(archive, manifest, original=False):
    for item in manifest['files']:
        name = item['source'] if original else item['target']
        info = archive.getinfo(name)
        if info.file_size != item['size']:
            raise ValueError('Wrong file size: ' + name)
        with archive.open(name) as stream:
            expected = item['sha256'] if original else item.get('target_sha256', item['sha256'])
            if digest(stream) != expected:
                raise ValueError('Unsupported or damaged game file: ' + name)


def prepare(gamedir, explicit_apk=None):
    gamedir = gamedir.resolve()
    manifest = json.loads((gamedir / 'tools/android-manifest.json').read_text())
    target = gamedir / 'game.port'
    source_apk = gamedir / 'assets/katanazero.apk'
    apks = [source_apk] if source_apk.is_file() else []
    if explicit_apk:
        apks = [explicit_apk.resolve()]
    if len(apks) > 1:
        raise ValueError('Keep only one Katana ZERO APK in assets.')
    if apks:
        source = apks[0]
        print('Checking the supplied Android YYC runner and game assets...', flush=True)
        temporary = gamedir / '.game.port.tmp'
        try:
            with zipfile.ZipFile(source) as original:
                verify(original, manifest, original=True)
                with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_STORED,
                                     allowZip64=True) as output:
                    for item in manifest['files']:
                        with original.open(item['source']) as incoming:
                            if item.get('patches'):
                                data = bytearray(incoming.read())
                                for patch in item['patches']:
                                    offset = patch['offset']
                                    before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
                                    if data[offset:offset + len(before)] != before:
                                        raise ValueError('Unexpected startup object; no compatibility edit applied.')
                                    data[offset:offset + len(before)] = after
                                output.writestr(item['target'], data)
                            else:
                                with output.open(item['target'], 'w', force_zip64=True) as outgoing:
                                    shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
            with zipfile.ZipFile(temporary) as output:
                verify(output, manifest)
            os.replace(temporary, target)
            print('Created game.port; original APK preserved.', flush=True)
            if not explicit_apk:
                # Retain the input without triggering another import on every launch.
                imported = source.with_name(source.name + '.imported')
                suffix = 1
                while imported.exists():
                    imported = source.with_name(source.name + '.imported.' + str(suffix))
                    suffix += 1
                source.rename(imported)
        finally:
            if temporary.exists():
                temporary.unlink()
    elif target.is_file():
        print('Checking the prepared Android YYC archive...', flush=True)
        with zipfile.ZipFile(target) as archive:
            verify(archive, manifest)
    else:
        raise ValueError('Rename the supported Katana ZERO v1.1.10 APK to katanazero.apk and copy it into katanazero/assets.')
    (gamedir / 'saves').mkdir(exist_ok=True)
    print('Android YYC preparation complete. Native game logic and textures are unchanged.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('gamedir', nargs='?', default='.')
    parser.add_argument('--apk', type=Path)
    args = parser.parse_args()
    try:
        prepare(Path(args.gamedir), args.apk)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print('Preparation failed: ' + str(error), file=sys.stderr, flush=True)
        sys.exit(1)
