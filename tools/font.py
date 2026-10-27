"""VWF font built from the game's own fullwidth Latin glyphs, trimmed to ink width.

Font sheet (ROM 0x5E7F7C): u16 glyphs per row (16), u16 tile rows, then 4bpp tiles.
Glyph g = 8x16 px: tiles at row (g>>4)*2 (+1 for bottom half), column g&15.
Background color 1 is treated as transparent.
"""
import font_glyphs
from script import _char_word

FONT_SHEET = 0x5E7F7C
GAP = 1           # extra advance after ink


def glyph_index(word: int) -> int:
    hi, lo = word >> 8, word & 0xFF
    return (hi - 0x81) * 0xC0 + (lo - 0x40)


def glyph_pixels(rom: bytes, g: int):
    per_row = int.from_bytes(rom[FONT_SHEET:FONT_SHEET + 2], 'little')
    data = FONT_SHEET + 4
    px = [[0] * 8 for _ in range(16)]
    for half in (0, 1):
        tile = ((g >> 4) * 2 + half) * per_row + (g & 15)
        base = data + tile * 32
        for y in range(8):
            for x in range(8):
                v = (rom[base + y * 4 + x // 2] >> (4 * (x & 1))) & 15
                px[half * 8 + y][x] = 0 if v == 1 else v
    return px


def render(c: str):
    """-> (16x8 pixel rows, advance) for our narrow font; ink=4, shadow=2 at (+1,+1)."""
    rows = font_glyphs.G[c]
    w = max((len(r.rstrip()) for r in rows), default=0)
    px = [[0] * 8 for _ in range(16)]
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '#':
                px[font_glyphs.TOP + y][x] = 4
    for y in range(15, 0, -1):
        for x in range(7, 0, -1):
            if px[y][x] == 0 and px[y - 1][x - 1] == 4:
                px[y][x] = 2
    adv = font_glyphs.SPACE_WIDTH if c == ' ' else w + GAP
    return px, adv


def build(rom: bytes):
    """-> (vwf_map: bytes[0x180], glyphs: bytes, widths: dict[str, int])"""
    vmap = bytearray(b'\xff' * 0x180)
    out = bytearray()
    widths = {}
    for n, c in enumerate(chr(i) for i in range(0x20, 0x7F)):
        px, adv = render(c)
        vmap[glyph_index(_char_word(c))] = n
        widths[c] = adv
        out.append(adv)
        for y in range(16):
            out += bytes(px[y][i] | px[y][i + 1] << 4 for i in range(0, 8, 2))
    out += bytes(65)      # 0x7F: blank, zero advance (pads DB titles, db.encode_title)
    return bytes(vmap), bytes(out), widths


def preview(text: str, path):
    """Render text lines on the textbox color for quick visual checks."""
    from PIL import Image
    pal = {0: (50, 42, 85), 2: (90, 80, 140), 4: (255, 255, 255)}
    lines = text.split('\n')
    im = Image.new('RGB', (224, 16 * len(lines)), pal[0])
    for ly, line in enumerate(lines):
        pen = 0
        for c in line:
            px, adv = render(c)
            for y in range(16):
                for x in range(min(8, adv + 1)):
                    if px[y][x] and pen + x < 224:
                        im.putpixel((pen + x, ly * 16 + y), pal[px[y][x]])
            pen += adv
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(path)
