"""L-menu database (EVENT / PERSON / OTHERS): three contiguous blobs at ROM 0x62F3A4.

Blob: u32 header = 4 x (offset, size) sections, offsets from blob start:
  0 titles   : u32 n, u32 off[n] (from section start), strings of SJIS words ending 0x0100
  1 pages    : u32 n, u32 off[n] (from section start), entry = u32 m, u32 page_off[m] (from section 3 start)
  2 order    : raw (u16 sort order), copied
  3 text     : pages, each 0x4010 <words, 0x0D0A = newline> 0x0100 0x4000
Only the first blob's address is referenced (literal pools); the others follow it, so the
rebuilt blobs are written back to back at a new address and the literals are repointed.

Entries can have several pages: alternative descriptions shown as the story progresses.

  python -m scripts.db extract        refresh text/db.json (keeps existing "en" fields)
  python -m scripts.db check "text"   lines the text needs on one page (max 4)
"""
import json
import struct
import sys

from scripts import ptr, rom
from scripts.extract import save_json
from scripts.insert import encode_checked
from scripts.script import decode_words
from scripts.wrap import normalize, wrap

BASE = 0x62F3A4
COUNT = 3
NEW = 0x1E40000
CRLF = 0x0D0A
PAGE_PX = 120          # description pane width
PAGE_LINES = 4
DB = rom.ROOT / 'text' / 'db.json'


def _words_until(buf, p, end=0x0100):
    ws = []
    while True:
        w = struct.unpack_from('<H', buf, p)[0]
        p += 2
        if w == end:
            return ws
        ws.append(w)


def parse(buf, base):
    hdr = struct.unpack_from('<8I', buf, base)
    sec = [base + hdr[2 * i] for i in range(4)]
    n = struct.unpack_from('<I', buf, sec[0])[0]
    titles = [_words_until(buf, sec[0] + o) for o in struct.unpack_from(f'<{n}I', buf, sec[0] + 4)]
    m = struct.unpack_from('<I', buf, sec[1])[0]
    pages = []
    for o in struct.unpack_from(f'<{m}I', buf, sec[1] + 4):
        k = struct.unpack_from('<I', buf, sec[1] + o)[0]
        offs = struct.unpack_from(f'<{k}I', buf, sec[1] + o + 4)
        pages.append([_words_until(buf, sec[3] + po + 2) for po in offs])   # skip leading 0x4010
    order = bytes(buf[sec[2]:sec[2] + hdr[5]])
    return {'titles': titles, 'pages': pages, 'order': order, 'size': hdr[6] + hdr[7]}


def blobs(buf):
    out, base = [], BASE
    for _ in range(COUNT):
        b = parse(buf, base)
        out.append(b)
        base += b['size']
    return out


def _pad(b: bytes) -> bytes:
    return b + b'\0' * (-len(b) % 4)


def _strlist(items):
    head = 4 + 4 * len(items)
    offs, body = [], b''
    for it in items:
        offs.append(head + len(body))
        body += it
    return _pad(struct.pack(f'<I{len(items)}I', len(items), *offs) + body)


def build_blob(titles, pages, order):
    """titles: word lists; pages: per entry list of page word lists."""
    words = lambda ws: struct.pack(f'<{len(ws)}H', *ws)
    sec0 = _strlist([words(t + [0x0100]) for t in titles])
    text, entries = b'', []
    for plist in pages:
        offs = []
        for p in plist:
            offs.append(len(text))
            text += words([0x4010] + p + [0x0100, 0x4000])
        entries.append(struct.pack(f'<I{len(offs)}I', len(offs), *offs))
    sec1 = _strlist(entries)
    sec2 = _pad(order)
    sec3 = _pad(text)
    hdr, pos, out = [], 0x20, b''
    for s in (sec0, sec1, sec2, sec3):
        hdr += [pos, len(s)]
        pos += len(s)
        out += s
    return struct.pack('<8I', *hdr) + out


def page_lines(text):
    from scripts import font
    return [l for page in wrap(normalize(text), font.build(b'')[2], PAGE_PX, 10 ** 6) for l in page]


def encode_page(text, where='db'):
    """EN text -> one page of words (0x0D0A newlines); must fit PAGE_LINES lines."""
    lines = page_lines(text)
    if len(lines) > PAGE_LINES:
        raise ValueError(f'{where}: {len(lines)} lines > {PAGE_LINES}: {text}')
    ws = []
    for i, line in enumerate(lines):
        if i:
            ws.append(CRLF)
        ws += encode_checked(line, where) if line else []
    return ws


def decode(ws):
    return decode_words([0x4001 if w == CRLF else w for w in ws])


def extract(buf):
    out = []
    for b, blob in enumerate(blobs(buf)):
        for i, (t, pg) in enumerate(zip(blob['titles'], blob['pages'])):
            out.append({'blob': b, 'id': i, 'title': decode(t), 'desc': [decode(p) for p in pg],
                        'title_en': '', 'desc_en': [''] * len(pg)})
    return out


def apply(buf: bytearray, entries=None):
    entries = entries if entries is not None else load()
    by = {(e['blob'], e['id']): e for e in entries}
    pos, data = NEW, b''
    moves, old = {}, BASE
    for b, blob in enumerate(blobs(bytes(buf))):
        moves[old] = NEW + len(data)
        old += blob['size']
        titles, pages = [], []
        for i, (t, pg) in enumerate(zip(blob['titles'], blob['pages'])):
            e = by.get((b, i), {})
            titles.append(encode_checked(normalize(e['title_en']), f'db {b}:{i}') if e.get('title_en') else t)
            en = e.get('desc_en') or []
            pages.append([encode_page(en[j], f'db {b}:{i}.{j}') if j < len(en) and en[j] else p
                          for j, p in enumerate(pg)])
        data += build_blob(titles, pages, blob['order'])
    buf[NEW:NEW + len(data)] = data
    found = ptr.sites(bytes(buf), list(moves))
    assert found[BASE], 'no database pointer found'
    for o, n in moves.items():
        for site in found[o]:
            ptr.write(buf, site, n)


def load():
    return json.loads(DB.read_text(encoding='utf-8')) if DB.exists() else []


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        lines = page_lines(sys.argv[2])
        print(f'{len(lines)} line(s)' + (' TOO LONG' if len(lines) > PAGE_LINES else ''), lines)
    if sys.argv[1] == 'extract':
        old = {(e['blob'], e['id']): e for e in load()}
        ents = extract(rom.load_clean())
        for e in ents:
            o = old.get((e['blob'], e['id']), {})
            e['title_en'] = o.get('title_en', '')
            e['desc_en'] = o.get('desc_en') or e['desc_en']
        save_json(DB, ents)
        print(len(ents), 'entries')
