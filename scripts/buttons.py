"""Title-menu buttons: ROM 0xBC62D0 = Huffman(4-bit) of LZ77 of a container
[u32 (offset, size) x4]: section 0 = tile sheet (u16 16 tiles wide, u16 14 rows, 4bpp), section 1 = palette.
Ten 64x16 buttons (unselected purple fill 1, selected orange fill 5; text color B)."""
import struct

from scripts import font_glyphs, huff, lz77

SRC = 0xBC62D0
NEW = 0x1EC0000
INK = 0xB
BUTTONS = [((0, 0), 'PLAY'), ((0, 16), 'SETTINGS'), ((0, 32), 'EXTRAS'),
           ((0, 48), 'PLAY'), ((0, 64), 'SETTINGS'), ((0, 80), 'EXTRAS'),
           ((64, 0), 'NEW GAME'), ((64, 16), 'CONTINUE'), ((64, 32), 'NEW GAME'), ((64, 48), 'CONTINUE')]


class Sheet:
    def __init__(self, data: bytearray, off: int):
        self.d, self.tw = data, struct.unpack_from('<H', data, off)[0]
        self.base = off + 4

    def _a(self, x, y):
        return self.base + ((y // 8) * self.tw + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2

    def get(self, x, y):
        return (self.d[self._a(x, y)] >> (4 * (x % 2))) & 15

    def put(self, x, y, v):
        a, sh = self._a(x, y), 4 * (x % 2)
        self.d[a] = (self.d[a] & (0xF0 >> sh)) | (v << sh)


def width(text):
    g = font_glyphs.G
    return sum(font_glyphs.SPACE_WIDTH if c == ' ' else max(len(r.rstrip()) for r in g[c]) + 1 for c in text) - 1


def redraw(container: bytearray):
    sheet = Sheet(container, struct.unpack_from('<I', container, 0)[0])
    for (x0, y0), text in BUTTONS:
        fill = sheet.get(x0 + 10, y0 + 4)
        for y in range(y0 + 3, y0 + 13):
            for x in range(x0 + 8, x0 + 56):
                sheet.put(x, y, fill)
        pen = x0 + 32 - width(text) // 2
        for c in text:
            if c == ' ':
                pen += font_glyphs.SPACE_WIDTH
                continue
            rows = font_glyphs.G[c]
            for dy, r in enumerate(rows[:9]):
                for dx, ch in enumerate(r):
                    if ch == '#':
                        sheet.put(pen + dx, y0 + 3 + dy, INK)
            pen += max(len(r.rstrip()) for r in rows) + 1


def apply(buf: bytearray):
    container = bytearray(lz77.decompress(huff.decompress(bytes(buf), SRC), 0))
    redraw(container)
    packed = huff.compress(lz77.compress(bytes(container)))
    buf[NEW:NEW + len(packed)] = packed
    words = memoryview(buf)[:0x1000000].cast('I')
    hits = [i for i, w in enumerate(words) if w == 0x08000000 | SRC]
    for i in hits:
        words[i] = 0x08000000 | NEW
    words.release()
    assert hits, 'no pointer to title buttons'
