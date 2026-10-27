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


def wrap(text: str, widths: dict, max_px: int, max_lines: int, start_px: int = 0, start_line: int = 0) -> list:
    """-> pages, each a list of <= max_lines lines no wider than max_px.
    start_px/start_line: where the text begins when it continues a fragment already in the box.
    Leading and trailing spaces are kept (fragments join on them)."""
    lines = []
    off = start_px
    for para in text.split('\n'):
        body = para.lstrip(' ')
        line = para[:len(para) - len(body)]
        for word in body.split(' '):
            for piece in _split_long(word, widths, max_px):
                cand = f'{line} {piece}' if line.strip() else line + piece
                if off + width(cand, widths) <= max_px:
                    line = cand
                elif line.strip() or off:
                    lines.append(line)
                    line, off = piece, 0
                else:
                    line = cand
        lines.append(line)
        off = 0
    first = max(1, max_lines - start_line)
    return [lines[:first]] + [lines[i:i + max_lines] for i in range(first, len(lines), max_lines)]
