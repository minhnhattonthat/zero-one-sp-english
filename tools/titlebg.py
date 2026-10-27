"""Title background (8bpp): ROM 0xBC3114 = Huffman(4-bit) of LZ77 of [sheet, palette, map].
Replaces the small 'SFアドベンチャー' subtitle under the logo with 'SF ADVENTURE' (3x5 font)."""
import struct

import ptr, huff, lz77
from labels import TINY

SRC = 0xBC3114
NEW = 0x1EE0000
RECT = (28, 73, 86, 80)           # x0, y0, x1, y1 cleared to BG
BG, INK = 0x04, 0x76
TEXT = 'SF ADVENTURE'
GLYPHS = dict(TINY, **{
    'S': ['###', '#..', '###', '..#', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'D': ['##.', '#.#', '#.#', '#.#', '##.'], 'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'], 'R': ['##.', '#.#', '##.', '#.#', '#.#']})


class Screen8:
    def __init__(self, c: bytes):
        self.c = c
        h = struct.unpack_from('<8I', c, 0)
        self.h = h
        self.tw, th = struct.unpack_from('<HH', c, h[0])
        self.tiles = [bytearray(c[h[0] + 4 + i * 64:h[0] + 4 + (i + 1) * 64]) for i in range(self.tw * th)]
        self.mw, self.mh = struct.unpack_from('<HH', c, h[4])
        self.map = list(struct.unpack_from(f'<{self.mw * self.mh}H', c, h[4] + 4))
        self.private = set()

    def _xy(self, x, y):
        e = self.map[(y // 8) * self.mw + x // 8]
        sx, sy = x % 8, y % 8
        if (e >> 10) & 1:
            sx = 7 - sx
        if (e >> 11) & 1:
            sy = 7 - sy
        return e, sy * 8 + sx

    def get(self, x, y):
        e, o = self._xy(x, y)
        return self.tiles[e & 0x3FF][o]

    def put(self, x, y, v):
        i = (y // 8) * self.mw + x // 8
        if i not in self.private:            # private, unflipped copy
            e = self.map[i]
            src = self.tiles[e & 0x3FF]
            hf, vf = (e >> 10) & 1, (e >> 11) & 1
            t = bytearray(src[(7 - yy if vf else yy) * 8 + (7 - xx if hf else xx)] for yy in range(8) for xx in range(8))
            self.tiles.append(t)
            self.map[i] = (e & 0xF000) | (len(self.tiles) - 1)
            self.private.add(i)
        self.tiles[self.map[i] & 0x3FF][(y % 8) * 8 + x % 8] = v

    def pack(self) -> bytes:
        while len(self.tiles) % self.tw:
            self.tiles.append(bytearray(64))
        sheet = struct.pack('<HH', self.tw, len(self.tiles) // self.tw) + b''.join(self.tiles)
        pal = bytes(self.c[self.h[2]:self.h[2] + self.h[3]])
        mp = struct.pack(f'<HH{len(self.map)}H', self.mw, self.mh, *self.map)
        secs = [s + b'\0' * (-len(s) % 4) for s in (sheet, pal, mp)]
        hdr, pos = [], 0x20
        for s in secs:
            hdr += [pos, len(s)]
            pos += len(s)
        return struct.pack('<8I', *hdr, 0, 0) + b''.join(secs)


def apply(buf: bytearray):
    scr = Screen8(lz77.decompress(huff.decompress(bytes(buf), SRC), 0))
    x0, y0, x1, y1 = RECT
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            scr.put(x, y, BG)
    pen = x0 + 2
    for c in TEXT:
        for dy, row in enumerate(GLYPHS[c]):
            for dx, ch in enumerate(row):
                if ch == '#':
                    scr.put(pen + dx, y0 + 1 + dy, INK)
        pen += len(GLYPHS[c][0]) + 1
    packed = huff.compress(lz77.compress(scr.pack()))
    assert NEW + len(packed) <= 0x1F00000, 'packed graphics overflow the next region'
    buf[NEW:NEW + len(packed)] = packed
    ptr.repoint(buf, {SRC: NEW})
