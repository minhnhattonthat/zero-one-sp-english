"""Pixel-width word wrapping for the VWF."""
import unicodedata

_REPL = {'’': "'", '‘': "'", '“': '"', '”': '"', '…': '...', '—': '-', '–': '-', '　': ' ', '～': '~'}


def normalize(s: str) -> str:
    for a, b in _REPL.items():
        s = s.replace(a, b)
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))


def width(line: str, widths: dict) -> int:
    return sum(widths.get(c, 8) for c in line)


def _split_long(word, widths, max_px):
    out, cur = [], ''
    for c in word:
        if cur and width(cur + c, widths) > max_px:
            out.append(cur)
            cur = ''
        cur += c
    return out + [cur]


def wrap(text: str, widths: dict, max_px: int, max_lines: int) -> list:
    """-> pages, each a list of <= max_lines lines no wider than max_px."""
    lines = []
    for para in text.split('\n'):
        cur = ''
        for word in para.split(' '):
            for piece in _split_long(word, widths, max_px):
                cand = f'{cur} {piece}' if cur else piece
                if cur and width(cand, widths) > max_px:
                    lines.append(cur)
                    cur = piece
                else:
                    cur = cand
        lines.append(cur)
    return [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)]
