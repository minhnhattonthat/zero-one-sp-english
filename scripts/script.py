"""Scene script block codec.

Block layout (decompressed): u32 header [0x10, offA, offB, offC]; u32 tables
0x10..offA and offA..offB plus offC are byte offsets relative to the bytecode,
which starts at offB and is a stream of u16 words. Text runs are SJIS words
(stored as (b0<<8)|b1) and 0x4001 line breaks, following a text-start opcode.
"""
import struct
from dataclasses import dataclass

TEXT_START = {0x4010, 0x4011, 0x4012, 0x4003}
NEWLINE = 0x4001


def is_text(w: int) -> bool:
    return w >= 0x8140 or w == NEWLINE


@dataclass
class Run:
    start: int      # word index of first text word
    end: int        # word index after last text word
    words: list
    prev: int       # opcode before the run
    next: int       # word after the run


class Block:
    def __init__(self, header, tables, words):
        self.header = header
        self.tables = tables
        self.words = words
        self.runs = []
        i = 0
        while i < len(words):
            if words[i] in TEXT_START and i + 1 < len(words) and is_text(words[i + 1]):
                j = i + 1
                while j < len(words) and is_text(words[j]):
                    j += 1
                nxt = words[j] if j < len(words) else None
                self.runs.append(Run(i + 1, j, list(words[i + 1:j]), words[i], nxt))
                i = j
            else:
                i += 1

    @classmethod
    def parse(cls, raw: bytes) -> 'Block':
        header = list(struct.unpack_from('<4I', raw))
        if header[0] != 0x10:
            raise ValueError('bad script header')
        base = header[2]
        tables = list(struct.unpack_from(f'<{(base - 16) // 4}I', raw, 16))
        words = list(struct.unpack_from(f'<{(len(raw) - base) // 2}H', raw, base))
        return cls(header, tables, words)

    def build(self, replacements: dict) -> bytes:
        """replacements: run index -> new word list. Shifts all offsets."""
        out = []
        shifts = []         # (old byte offset of run end, cumulative delta)
        pos = 0
        delta = 0
        for k, run in enumerate(self.runs):
            out += self.words[pos:run.start]
            new = replacements.get(k, run.words)
            out += new
            delta += 2 * (len(new) - len(run.words))
            shifts.append((run.end * 2, delta))
            pos = run.end
        out += self.words[pos:]

        def fix(o):
            d = 0
            for end, cum in shifts:
                if end <= o:
                    d = cum
                else:
                    break
            return o + d

        tables = [fix(o) for o in self.tables]
        header = self.header[:3] + [fix(self.header[3])]
        return (struct.pack('<4I', *header) + struct.pack(f'<{len(tables)}I', *tables)
                + struct.pack(f'<{len(out)}H', *out))


# EN <-> fullwidth SJIS
_SPECIAL = {' ': '　', "'": '’', '"': '”', '`': '‘', '~': '～', '-': '－', '\\': '＼'}


def _char_word(c: str) -> int:
    fw = _SPECIAL.get(c) or (chr(ord(c) + 0xFEE0) if 0x21 <= ord(c) <= 0x7E else c)
    try:
        b = fw.encode('cp932')
    except UnicodeEncodeError:
        raise ValueError(f'unencodable char {c!r}') from None
    if len(b) != 2:
        raise ValueError(f'unencodable char {c!r}')
    return b[0] << 8 | b[1]


def encode_text(s: str) -> list:
    return [NEWLINE if c == '\n' else _char_word(c) for c in s]


def decode_words(ws) -> str:
    out = []
    for w in ws:
        if w == NEWLINE:
            out.append('\n')
        else:
            try:
                out.append(bytes((w >> 8, w & 0xFF)).decode('cp932'))
            except UnicodeDecodeError:
                out.append('{%04X}' % w)
    return ''.join(out)
