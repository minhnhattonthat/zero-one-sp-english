"""UI/system strings (save/load, retry menus, game-over hints, ending list...).

Plain SJIS (normal byte order), 0x0A newline, control bytes < 0x20 kept as {XX}, NUL-terminated,
referenced by aligned pointers. Translated strings are written to free space and every pointer is moved.

  python -m scripts.ui extract     refresh text/ui.json (keeps existing "en")
"""
import json
import re

from scripts import rom
from scripts.extract import save_json
from scripts.insert import encode_checked
from scripts.wrap import normalize

REGION = (0xF9000, 0xFD800)
SKIP = {0xFA29C}          # chapter titles: fixed 5-byte records, handled separately
FREE = 0x1E00000
UI = rom.ROOT / 'text' / 'ui.json'


def decode(b: bytes):
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if c == 0x0A:
            out.append('\n')
            i += 1
        elif c < 0x20:
            out.append('{%02X}' % c)
            i += 1
        elif 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xEF:
            out.append(b[i:i + 2].decode('cp932'))
            i += 2
        else:
            raise ValueError
    return ''.join(out)


def encode(s: str) -> bytes:
    """EN text (ASCII + {XX} controls) -> fullwidth SJIS bytes."""
    out = bytearray()
    for part in re.split(r'(\{[0-9A-F]{2}\}|\n)', s):
        if not part:
            continue
        if part == '\n':
            out.append(0x0A)
        elif re.fullmatch(r'\{[0-9A-F]{2}\}', part):
            out.append(int(part[1:3], 16))
        else:
            for w in encode_checked(part, 'ui'):
                out += bytes((w >> 8, w & 0xFF))
    return bytes(out)


PTR_LIMIT = 0x400000      # code + rodata tables; matches beyond this are coincidences inside graphics


def pointer_sites(buf: bytes, addrs):
    want = {0x08000000 | a: a for a in addrs}
    sites = {a: [] for a in addrs}
    for k, v in enumerate(memoryview(buf[:PTR_LIMIT]).cast('I')):
        if v in want:
            sites[want[v]].append(k * 4)
    return sites


def extract(r: bytes) -> list:
    """Every pointer target inside REGION that decodes as a JP string (up to its NUL)."""
    lo, hi = 0x08000000 | REGION[0], 0x08000000 | REGION[1]
    targets = sorted({v & 0xFFFFFF for v in memoryview(r[:PTR_LIMIT]).cast('I') if lo <= v < hi})
    out = []
    for a in targets:
        if a in SKIP:
            continue
        try:
            t = decode(r[a:r.find(b'\0', a)])
        except (ValueError, UnicodeDecodeError):
            continue
        if re.search(r'[　-〿぀-ヿ一-鿿！-～]', t):
            out.append({'addr': hex(a), 'jp': t, 'en': ''})
    return out


def apply(buf: bytearray, entries: list):
    todo = [e for e in entries if e['en']]
    sites = pointer_sites(bytes(buf), [int(e['addr'], 16) for e in todo])
    pos = FREE
    for e in todo:
        data = encode(normalize(e['en'])) + b'\0'
        buf[pos:pos + len(data)] = data
        for s in sites[int(e['addr'], 16)]:
            buf[s:s + 4] = (0x08000000 | pos).to_bytes(4, 'little')
        pos += -(-len(data) // 4) * 4
    assert pos < 0x1F00000


def load() -> list:
    return json.loads(UI.read_text(encoding='utf-8')) if UI.exists() else []


if __name__ == '__main__':
    old = {e['addr']: e['en'] for e in load()}
    ents = extract(rom.load_clean())
    for e in ents:
        e['en'] = old.get(e['addr'], '')
    save_json(UI, ents)
    print(len(ents), 'ui strings')
