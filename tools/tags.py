"""Speaker name tags: 60 raw 4bpp 64x16 labels at ROM 0x63BCC0 (tag id = speaker id).
Each tag = 8 top tiles then 8 bottom tiles. Interior stripes: color 8 on odd rows, 9 on even rows
(rows 3..12); JP label drawn in colors 6/7. We clear the label and draw the English name in caps."""
import json

import font_glyphs
from rom import ROOT

BASE = 0x63BCC0
COUNT = 60
X0, X1 = 4, 58                 # usable interior columns
TOP = 3                        # tag row for glyph row 0
SHORT = {"Mita's Mother": "MITA'S MOM", 'Forensics Officer': 'FORENSICS', 'Announcement': 'ANNOUNCER',
         'Chairman Yaoi': 'YAOI', 'Newscaster': 'ANCHOR', 'SDF Officer': 'SOLDIER', 'Hotel Clerk': 'CLERK',
         'Detective?': 'DET.?', 'Detective A': 'DET. A', 'Detective B': 'DET. B'}


def labels():
    names = json.loads((ROOT / 'script' / 'speakers.json').read_text(encoding='utf-8'))
    return {int(k): SHORT.get(v, v.upper()) for k, v in names.items() if v}


def read(buf, k):
    base = BASE + k * 0x200
    px = [[0] * 64 for _ in range(16)]
    for half in (0, 1):
        for t in range(8):
            a = base + half * 0x100 + t * 32
            for y in range(8):
                for x in range(8):
                    px[half * 8 + y][t * 8 + x] = (buf[a + y * 4 + x // 2] >> (4 * (x & 1))) & 15
    return px


def write(buf, k, px):
    base = BASE + k * 0x200
    for half in (0, 1):
        for t in range(8):
            a = base + half * 0x100 + t * 32
            for y in range(8):
                for x in range(0, 8, 2):
                    buf[a + y * 4 + x // 2] = px[half * 8 + y][t * 8 + x] | px[half * 8 + y][t * 8 + x + 1] << 4


def text_width(s, gap):
    g = font_glyphs.G
    return sum((font_glyphs.SPACE_WIDTH if c == ' ' else max(len(r.rstrip()) for r in g[c]) + gap) for c in s)


def render(px, text):
    for y in range(3, 13):
        for x in range(3, 58):
            frame = (0, 1, 8, 9, 10) if x < 8 or x > 56 else (8, 9)   # edges hold the frame's diagonals
            if px[y][x] not in frame:
                px[y][x] = 8 if y % 2 else 9
    gap = 1 if text_width(text, 1) <= X1 - X0 else 0
    w = text_width(text, gap)
    if w > X1 - X0 + 1:
        raise ValueError(f'tag too wide: {text} ({w}px)')
    pen = X0 + (X1 - X0 - w) // 2
    for c in text:
        if c == ' ':
            pen += font_glyphs.SPACE_WIDTH
            continue
        rows = font_glyphs.G[c]
        for y, r in enumerate(rows[:9]):
            for x, ch in enumerate(r):
                if ch == '#':
                    px[TOP + y][pen + x] = 6
        pen += max(len(r.rstrip()) for r in rows) + gap
    return px


def apply(buf):
    for k, text in labels().items():
        write(buf, k, render(read(buf, k), text))
