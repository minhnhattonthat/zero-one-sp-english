"""Small JP labels in the UI sheet at ROM 0x6391F8 (u16 16 tiles wide, u16 rows, 4bpp tiles):
'SELECT で時間順表示' / 'SELECT で名前順表示' (48x8 px each). Redrawn with a 3x5 font."""
SHEET = 0x6391F8
TILES_W = 16
BG, INK = 0xB, 0x5
LABELS = [((80, 32), 'BY TIME'), ((80, 40), 'BY NAME')]
TINY = {'B': ['##.', '#.#', '##.', '#.#', '##.'], 'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'],
        'T': ['###', '.#.', '.#.', '.#.', '.#.'], 'I': ['###', '.#.', '.#.', '.#.', '###'],
        'M': ['#.#', '###', '###', '#.#', '#.#'], 'E': ['###', '#..', '##.', '#..', '###'],
        'N': ['#.#', '###', '###', '###', '#.#'], 'A': ['.#.', '#.#', '###', '#.#', '#.#'], ' ': ['.', '.', '.', '.', '.']}


def _addr(x, y):
    t = (y // 8) * TILES_W + x // 8
    return SHEET + 4 + t * 32 + (y % 8) * 4 + (x % 8) // 2


def put(buf, x, y, v):
    a = _addr(x, y)
    sh = 4 * (x % 2)
    buf[a] = (buf[a] & ~(0xF << sh) & 0xFF) | (v << sh)


def apply(buf):
    for (x0, y0), text in LABELS:
        for y in range(y0, y0 + 8):
            for x in range(x0, x0 + 48):
                put(buf, x, y, BG)
        pen = x0 + 2
        for c in text:
            for dy, row in enumerate(TINY[c]):
                for dx, ch in enumerate(row):
                    if ch == '#':
                        put(buf, pen + dx, y0 + 1 + dy, INK)
            pen += len(TINY[c][0]) + 1
