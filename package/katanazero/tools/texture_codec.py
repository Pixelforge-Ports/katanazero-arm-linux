"""YYG QOI decoder adapted from JeodC/gmtoolkit Codec/Qoif.cpp (MIT).

Source revision f23093e4a6e3ab3424e536c5a93c0f9464681b91.
See license/texture-codec.LICENSE. Only the texture encoding is changed.
"""
import bz2
import struct
import zlib


def stub(index):
    # QOI textures bypass this runner's PNG hook; use actual PNG placeholders.
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag+data))
    pixels = b'\0\xde\xad\xbe\xff' + struct.pack('<I', index | 0xff000000)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 1, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b''))


def decode(blob):
    """Decode the supported APK's BZip2-wrapped YYG QOI to straight RGBA."""
    if blob[:4] != b'2zoq' or blob[12:15] != b'BZh':
        raise ValueError('Unsupported texture encoding.')
    data = bz2.decompress(blob[12:])
    if data[:4] != b'fioq' or len(data) != struct.unpack_from('<I', blob, 8)[0]:
        raise ValueError('Invalid YYG texture stream.')
    width, height = struct.unpack_from('<HH', data, 4)
    if (width, height) != struct.unpack_from('<HH', blob, 4):
        raise ValueError('Texture dimensions do not match.')
    output = bytearray(width * height * 4)
    cache = [b'\0\0\0\0'] * 64
    pixel = [0, 0, 0, 255]
    cursor, written = 12, 0

    def sx(value, bits):
        value &= (1 << bits)-1
        return value-(1 << bits) if value & (1 << (bits-1)) else value

    while written < len(output):
        if cursor >= len(data):
            raise ValueError('Truncated texture stream.')
        opcode = data[cursor]
        cursor += 1
        run, update = 0, True
        if opcode < 0x40:
            pixel = list(cache[opcode])
            update = False
        elif opcode < 0x60:
            run, update = opcode & 31, False
        elif opcode < 0x80:
            run, update = ((opcode & 31) << 8 | data[cursor]) + 32, False
            cursor += 1
        elif opcode < 0xc0:
            pixel[:3] = [(pixel[i] + sx(opcode >> (4-2*i), 2)) & 255 for i in range(3)]
        elif opcode < 0xe0:
            second = data[cursor]
            cursor += 1
            deltas = (sx(opcode, 5), sx(second >> 4, 4), sx(second, 4))
            pixel[:3] = [(pixel[i] + deltas[i]) & 255 for i in range(3)]
        elif opcode < 0xf0:
            second, third = data[cursor:cursor+2]
            cursor += 2
            deltas = (sx((opcode & 15) << 1 | second >> 7, 5), sx(second, 7) >> 2,
                      sx((second & 3) << 8 | third, 10) >> 5, sx(third, 5))
            pixel = [(pixel[i] + deltas[i]) & 255 for i in range(4)]
        else:
            for i in range(4):
                if opcode & (8 >> i):
                    pixel[i] = data[cursor]
                    cursor += 1
        packed = bytes(pixel)
        if update:
            cache[(pixel[0] ^ pixel[1] ^ pixel[2] ^ pixel[3]) & 63] = packed
        block = packed * (run+1)
        if written+len(block) > len(output):
            raise ValueError('Texture run exceeds image size.')
        output[written:written+len(block)] = block
        written += len(block)
    return output, width, height


def tga(rgba, width, height):
    bgra = bytearray(rgba)
    bgra[0::4], bgra[2::4] = rgba[2::4], rgba[0::4]
    return struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, width, height, 32, 0x28) + bgra
