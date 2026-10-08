"""Chapter title cards (big '悪夢' etc. shown at scene start): 20 blobs listed at ROM 0x3AFAC0,
each Huffman(4-bit) of LZ77 of a [sheet, palette, map] container (same layout as the options screen).
The kanji are cleared and the English title is drawn at 2x scale."""
import struct

from scripts import font_glyphs, huff, lz77
from scripts.options import Screen, glyph_width
from scripts.titles import TITLES

TABLE = 0x3AFAC0
NEW = 0x1ED0000
CLEAR = (24, 56, 215, 103)       # x0, y0, x1, y1
SCALE = 2


def card_colors(scr):
    """(background index = most common in the card area, ink = brightest palette entry)"""
    import collections
    x0, y0, x1, y1 = CLEAR
    bg = collections.Counter(scr.get(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)).most_common(1)[0][0]
    h = struct.unpack_from('<8I', scr.c, 0)
    pal = struct.unpack_from('<16H', scr.c, h[2])
    lum = lambda v: (v & 31) + ((v >> 5) & 31) + ((v >> 10) & 31)
    return bg, max(range(16), key=lambda i: lum(pal[i]))


def draw_title(scr, text):
    x0, y0, x1, y1 = CLEAR
    bg, ink = card_colors(scr)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if scr.get(x, y) != bg:
                scr.put(x, y, bg)
    w = (sum(glyph_width(c) for c in text) - 1) * SCALE
    pen, top = 120 - w // 2, 80 - 9 * SCALE // 2
    for c in text:
        if c != ' ':
            for dy, r in enumerate(font_glyphs.G[c][:9]):
                for dx, ch in enumerate(r):
                    if ch == '#':
                        for sy in range(SCALE):
                            for sx in range(SCALE):
                                scr.put(pen + dx * SCALE + sx, top + dy * SCALE + sy, ink)
        pen += glyph_width(c) * SCALE


def apply(buf: bytearray):
    ptrs = struct.unpack_from('<20I', buf, TABLE)
    want = set(ptrs)
    sites = {}
    for k, w in enumerate(memoryview(buf)[:0x1000000].cast('I')):
        if w in want:
            sites.setdefault(w, []).append(k * 4)
    pos = NEW
    for i, (p, title) in enumerate(zip(ptrs, TITLES)):
        src = p - 0x08000000
        scr = Screen(bytearray(lz77.decompress(huff.decompress(bytes(buf), src), 0)))
        draw_title(scr, title.upper())
        packed = huff.compress(lz77.compress(scr.pack()))
        buf[pos:pos + len(packed)] = packed
        for site in sites[p]:
            buf[site:site + 4] = (0x08000000 | pos).to_bytes(4, 'little')
        pos += -(-len(packed) // 4) * 4
    assert pos < 0x1EE0000
