#!/usr/bin/env python3
"""Apply the runner's full-scale flag to a verified prepared game, preserving its camera."""
import copy
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import zipfile

from android_compat import digest, verify


def configure(gamedir):
    gamedir = gamedir.resolve()
    preference = gamedir / 'display_mode.txt'
    mode = preference.read_text().strip().lower() if preference.is_file() else 'full'
    if mode not in ('full', 'original'):
        raise ValueError('display_mode.txt must contain full or original.')
    target = gamedir / 'game.port'
    with zipfile.ZipFile(target) as original:
        with original.open('assets/game.droid') as incoming:
            header = incoming.read(88)
        if header[8:12] != b'GEN8' or len(header) != 88:
            raise ValueError('Unsupported game header; display settings were not changed.')
        flags, = struct.unpack_from('<I', header, 84)
        desired = flags & ~0x10 if mode == 'full' else flags | 0x10
        if flags == desired:
            print('Display mode: ' + mode + '.', flush=True)
            return
        manifest = json.loads((gamedir / 'tools/android-manifest.json').read_text())
        verify(original, manifest)
        if len(original.namelist()) != len(set(original.namelist())):
            raise ValueError('Duplicate archive entries; display settings were not changed.')
        descriptor, name = tempfile.mkstemp(prefix='.display-', suffix='.tmp', dir=gamedir)
        os.close(descriptor)
        temporary = Path(name)
        try:
            print('Applying display mode: ' + mode + '...', flush=True)
            with zipfile.ZipFile(temporary, 'w', allowZip64=True) as output:
                output.comment = original.comment
                for info in original.infolist():
                    if info.filename == 'assets/game.droid':
                        data = bytearray(original.read(info))
                        struct.pack_into('<I', data, 84, desired)
                        output.writestr(copy.copy(info), data)
                    else:
                        with original.open(info) as incoming, output.open(copy.copy(info), 'w') as outgoing:
                            shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
            with zipfile.ZipFile(temporary) as candidate:
                verify(candidate, manifest)
                expected = next(item for item in manifest['files'] if item['target'] == 'assets/game.droid')
                with candidate.open('assets/game.droid') as incoming:
                    required = {expected['fullscale_sha256'], expected.get('astc4x4_fullscale_sha256')} if mode == 'full' else {
                        expected['target_sha256'], expected.get('astc4x4_sha256')}
                    if digest(incoming) not in required:
                        raise ValueError('Display conversion failed verification; existing game preserved.')
            original.close()
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()
    print('Display mode: ' + mode + '. Saves and game content preserved.', flush=True)


if __name__ == '__main__':
    try:
        configure(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print('Display setup failed: ' + str(error), file=sys.stderr, flush=True)
        sys.exit(1)
