"""Options screen (single BG): ROM 0xBC117C = Huffman(4-bit) of LZ77 of a container
[(offset, size) x4]: 0 = tile sheet (u16 16 tiles wide, u16 rows), 1 = palettes, 2 = map (u16 w=30, h=20, entries).
Edited map cells get private tile copies (appended to the sheet) so shared tiles stay intact."""
import struct

from scripts import ptr, font_glyphs, huff, lz77

SRC = 0xBC117C
NEW = 0x1EC8000
MAX_TILES = (0xF800 - 0xC000) // 32      # BG1 char base 0xC000 .. screen base 0xF800

LEFT = ['MESSAGE SPEED', 'SFX AS TEXT', 'EVENT SKIP', 'MESSAGE SKIP', 'ERASE SAVE']
SPEED = ['FAST', 'MED', 'SLOW', 'ALL']
# (x0, y0, x1, y1) interior rects (inclusive), fill rule, ink, text, bold
EDITS = ([(14, 34 + 24 * r, 90, 45 + 24 * r, 1, 4, t, False) for r, t in enumerate(LEFT)]
         + [(111 + 32 * i, 34, 128 + 32 * i, 45, 1, 4, t, False) for i, t in enumerate(SPEED)]
         + [(x, 34 + 24 * r, x + 26, 45 + 24 * r, 1, 4, t, False)
            for r in (1, 2, 4) for x, t in ((134, 'OFF'), (182, 'ON'))]
         + [(110, 4, 222, 16, 'stripe', 0xB, 'OPTIONS', True)])


class Screen:
    def __init__(self, c: bytearray):
        self.c = c
        h = struct.unpack_from('<8I', c, 0)
        self.sheet_off, self.map_off = h[0], h[4]
        self.tw, self.th = struct.unpack_from('<HH', c, self.sheet_off)
        self.mw, self.mh = struct.unpack_from('<HH', c, self.map_off)
        self.map = list(struct.unpack_from(f'<{self.mw * self.mh}H', c, self.map_off + 4))
        n = self.tw * self.th
        tiles = c[self.sheet_off + 4:self.sheet_off + 4 + n * 32]
        self.tiles = [bytearray(tiles[i * 32:(i + 1) * 32]) for i in range(n)]
        self.private = set()

    def _cell(self, x, y):
        return (y // 8) * self.mw + x // 8

    def own(self, x, y):
        """Give map cell under (x, y) a private, unflipped tile."""
        i = self._cell(x, y)
        if i in self.private:
            return
        e = self.map[i]
        src, hf, vf = self.tiles[e & 0x3FF], (e >> 10) & 1, (e >> 11) & 1
        t = bytearray(32)
        for yy in range(8):
            for xx in range(8):
                sx, sy = (7 - xx if hf else xx), (7 - yy if vf else yy)
                v = (src[sy * 4 + sx // 2] >> (4 * (sx & 1))) & 15
                t[yy * 4 + xx // 2] |= v << (4 * (xx & 1))
        self.tiles.append(t)
        self.map[i] = (e & 0xF000) | (len(self.tiles) - 1)
        self.private.add(i)

    def get(self, x, y):
        e = self.map[self._cell(x, y)]
        sx, sy = x % 8, y % 8
        if (e >> 10) & 1:
            sx = 7 - sx
        if (e >> 11) & 1:
            sy = 7 - sy
        return (self.tiles[e & 0x3FF][sy * 4 + sx // 2] >> (4 * (sx & 1))) & 15

    def put(self, x, y, v):
        self.own(x, y)
        t = self.tiles[self.map[self._cell(x, y)] & 0x3FF]
        a, sh = (y % 8) * 4 + (x % 8) // 2, 4 * (x % 2)
        t[a] = (t[a] & (0xF0 >> sh)) | (v << sh)

    @staticmethod
    def _flip(t, hf, vf):
        out = bytearray(32)
        for y in range(8):
            for x in range(8):
                sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                out[y * 4 + x // 2] |= ((t[sy * 4 + sx // 2] >> (4 * (sx & 1))) & 15) << (4 * (x & 1))
        return bytes(out)

    def dedupe(self):
        """Rebuild the tile list from the map, sharing identical tiles (also via h/v flips)."""
        seen, tiles, new_map = {}, [], []
        for e in self.map:
            t = bytes(self.tiles[e & 0x3FF])
            hf0, vf0 = (e >> 10) & 1, (e >> 11) & 1
            for hf in (0, 1):
                for vf in (0, 1):
                    key = self._flip(t, hf, vf)
                    if key in seen:
                        idx = seen[key]
                        new_map.append((e & 0xF000) | ((hf ^ hf0) << 10) | ((vf ^ vf0) << 11) | idx)
                        break
                else:
                    continue
                break
            else:
                seen[t] = len(tiles)
                tiles.append(bytearray(t))
                new_map.append(e & 0xFFFF)
                new_map[-1] = (e & 0xFC00) | (len(tiles) - 1)
        self.tiles, self.map = tiles, new_map

    def pack(self) -> bytes:
        self.dedupe()
        if len(self.tiles) > MAX_TILES:
            raise ValueError(f'options screen needs {len(self.tiles)} tiles > {MAX_TILES}')
        while len(self.tiles) % self.tw:
            self.tiles.append(bytearray(32))
        sheet = struct.pack('<HH', self.tw, len(self.tiles) // self.tw) + b''.join(self.tiles)
        h = struct.unpack_from('<8I', self.c, 0)
        pal = bytes(self.c[h[2]:h[2] + h[3]])
        mp = struct.pack(f'<HH{len(self.map)}H', self.mw, self.mh, *self.map)
        secs = [sheet, pal, mp]
        secs = [s + b'\0' * (-len(s) % 4) for s in secs]
        hdr, pos = [], 0x20
        for s in secs:
            hdr += [pos, len(s)]
            pos += len(s)
        return struct.pack('<8I', *hdr, 0, 0) + b''.join(secs)


def glyph_width(c):
    return font_glyphs.SPACE_WIDTH if c == ' ' else max(len(r.rstrip()) for r in font_glyphs.G[c]) + 1


def draw(scr, x0, y0, x1, y1, fill, ink, text, bold):
    for y in range(y0, y1 + 1):
        f = (0xA if y % 2 == 0 else 0x7) if fill == 'stripe' else fill
        for x in range(x0, x1 + 1):
            scr.put(x, y, f)
    gap = 1 if sum(glyph_width(c) for c in text) - 1 <= x1 - x0 + 1 else 0   # tighten if too wide
    adv = lambda c: glyph_width(c) - 1 + gap + (1 if bold else 0)
    w = sum(adv(c) for c in text) - gap
    pen = x0 + (x1 - x0 + 1 - w) // 2
    top = y0 + (y1 - y0 + 1 - 9) // 2
    for c in text:
        if c != ' ':
            for dy, r in enumerate(font_glyphs.G[c][:9]):
                for dx, ch in enumerate(r):
                    if ch == '#':
                        scr.put(pen + dx, top + dy, ink)
                        if bold:
                            scr.put(pen + dx + 1, top + dy, ink)
        pen += adv(c)


def apply(buf: bytearray):
    scr = Screen(bytearray(lz77.decompress(huff.decompress(bytes(buf), SRC), 0)))
    for e in EDITS:
        draw(scr, *e)
    packed = huff.compress(lz77.compress(scr.pack()))
    buf[NEW:NEW + len(packed)] = packed
    ptr.repoint(buf, {SRC: NEW})
