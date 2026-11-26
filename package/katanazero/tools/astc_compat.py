#!/usr/bin/env python3
"""Convert the supported Android texture pages to gmloader-next ASTC 4x4 PVRs."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

from android_compat import digest, verify
from texture_codec import decode, stub, tga


def pvr_valid(path, page, expected_hash=None):
    size = ((page['width']+3)//4)*((page['height']+3)//4)*16
    header = struct.pack('<IIQ9I', 0x03525650, 0, 27, 0, 0, page['height'], page['width'], 1, 1, 1, 1, 0)
    if not path.is_file() or path.stat().st_size != 52+size:
        return False
    with path.open('rb') as incoming:
        if incoming.read(52) != header:
            return False
        incoming.seek(0)
        return expected_hash is None or digest(incoming) == expected_hash


def prepare(gamedir, encoder):
    gamedir = gamedir.resolve()
    manifest = json.loads((gamedir / 'tools/android-manifest.json').read_text())
    textures = json.loads((gamedir / 'tools/astc4x4-manifest.json').read_text())
    target = gamedir / 'game.port'
    state_path = gamedir / '.astc4x4.json'
    destination = gamedir / 'saves/textures'
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    with zipfile.ZipFile(target) as archive:
        verify(archive, manifest)
        data = bytearray(archive.read('assets/game.droid'))
    current_hash = hashlib.sha256(data).hexdigest()
    selected_flags, = struct.unpack_from('<I', data, 84)
    patched_hashes = (textures['original_view_sha256'], textures['full_view_sha256'])
    if current_hash in patched_hashes:
        hashes = state.get('textures', {})
        if state.get('version') == textures['version'] and all(
                str(page['index']) in hashes and pvr_valid(destination / f"{page['index']}.pvr", page,
                    hashes[str(page['index'])]) for page in textures['pages']):
            print('ASTC 4x4 textures verified.', flush=True)
            return
        # Recover missing/damaged textures from the retained prepared-game backup.
        with zipfile.ZipFile(gamedir / '.game.pre-astc.port') as archive:
            verify(archive, manifest)
            data = bytearray(archive.read('assets/game.droid'))
        if hashlib.sha256(data).hexdigest() in patched_hashes:
            raise ValueError('The pre-ASTC backup is not an original prepared game.')
        # Preserve the currently selected display mode during repair.
        struct.pack_into('<I', data, 84, selected_flags)
    if not encoder.is_file() or not os.access(encoder, os.X_OK):
        raise ValueError('PortMaster ASTC encoder missing. Update PortMaster and retry.')
    # Cached hashes remain usable in memory, but an interrupted rebuild must retry.
    if state_path.exists():
        state_path.unlink()
    with tempfile.TemporaryDirectory(prefix='.astc4x4-', dir=gamedir) as temporary:
        work = Path(temporary).resolve()
        assert work.parent == gamedir
        hashes = {}
        for number, page in enumerate(textures['pages'], 1):
            index = page['index']
            offset, size = page['offset'], page['size']
            source = bytes(data[offset:offset+size])
            if hashlib.sha256(source).hexdigest() != page['source_sha256']:
                raise ValueError('Unsupported texture page: ' + str(index))
            print(f'ASTC 4x4 texture {number}/{len(textures["pages"])} ({page["width"]}x{page["height"]})', flush=True)
            output = work / f'{index}.pvr'
            cached = destination / output.name
            old_hash = state.get('textures', {}).get(str(index))
            if old_hash and pvr_valid(cached, page, old_hash):
                shutil.copyfile(cached, output)
            else:
                rgba, width, height = decode(source)
                if (width, height) != (page['width'], page['height']):
                    raise ValueError('Unexpected texture dimensions.')
                image, astc = work / 'page.tga', work / 'page.astc'
                image.write_bytes(tga(rgba, width, height))
                del rgba
                subprocess.run([str(encoder), '-cl', str(image), str(astc), '4x4', '-medium', '-j', '2', '-silent'], check=True)
                encoded = astc.read_bytes()
                expected_header = b'\x13\xab\xa1\x5c\x04\x04\x01' + width.to_bytes(3, 'little') + height.to_bytes(3, 'little') + b'\x01\x00\x00'
                if encoded[:16] != expected_header:
                    raise ValueError('Encoder returned an unexpected ASTC format.')
                output.write_bytes(struct.pack('<IIQ9I', 0x03525650, 0, 27, 0, 0, height, width, 1, 1, 1, 1, 0) + encoded[16:])
                image.unlink()
                astc.unlink()
            if not pvr_valid(output, page):
                raise ValueError('Invalid ASTC PVR output: ' + str(index))
            with output.open('rb') as incoming:
                hashes[str(index)] = digest(incoming)
            replacement = stub(index)
            data[offset:offset+size] = replacement + b'\0'*(size-len(replacement))
            struct.pack_into('<I', data, page['size_offset'], len(replacement))
        if hashlib.sha256(data).hexdigest() not in patched_hashes:
            raise ValueError('Texture conversion failed verification; original game preserved.')
        candidate = work / 'game.port'
        with zipfile.ZipFile(target) as original, zipfile.ZipFile(candidate, 'w', allowZip64=True) as output:
            output.comment = original.comment
            for info in original.infolist():
                entry = copy.copy(info)
                if info.filename == 'assets/game.droid':
                    # Zero-filled texture slots compress well; preserve every original file offset.
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    output.writestr(entry, data)
                else:
                    with original.open(info) as incoming, output.open(entry, 'w') as outgoing:
                        shutil.copyfileobj(incoming, outgoing, 1024*1024)
        with zipfile.ZipFile(candidate) as archive:
            verify(archive, manifest)
        backup = gamedir / '.game.pre-astc.port'
        if not backup.exists():
            shutil.copyfile(target, backup)
        destination.mkdir(parents=True, exist_ok=True)
        for page in textures['pages']:
            name = f"{page['index']}.pvr"
            os.replace(work / name, destination / name)
        os.replace(candidate, target)
        marker = work / 'state.json'
        marker.write_text(json.dumps({'version': textures['version'], 'block': '4x4', 'textures': hashes}, indent=2)+'\n')
        os.replace(marker, state_path)
    print('ASTC 4x4 preparation complete. Original prepared game retained as .game.pre-astc.port.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('gamedir', type=Path)
    parser.add_argument('--encoder', type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.gamedir, args.encoder)
    except (OSError, ValueError, KeyError, IndexError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print('ASTC preparation failed: ' + str(error), file=sys.stderr, flush=True)
        sys.exit(1)
