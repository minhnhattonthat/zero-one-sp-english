"""Find packed graphics: decode every BIOS Huffman (0x24/0x28, then LZ77 if nested) stream in a ROM range
and report which blobs contain given tiles. Cache in build/gfxscan.pkl."""
import pickle

import lz77
from rom import ROOT, load_clean

CACHE = ROOT / 'build' / 'gfxscan.pkl'


def _huff(data, off, limit=0x40000):
    bits = data[off] & 15
    size = int.from_bytes(data[off + 1:off + 4], 'little')
    if bits not in (4, 8) or not 0x40 <= size <= limit:
        return None
    tree = off + 4
    root, p = tree + 1, tree + (data[tree] + 1) * 2
    out, acc, nacc, node, words = bytearray(), 0, 0, tree + 1, 0
    while len(out) < size:
        if p + 4 > len(data) or words > size:
            return None
        word = int.from_bytes(data[p:p + 4], 'little')
        p += 4
        words += 1
        for b in range(31, -1, -1):
            bit = (word >> b) & 1
            v = data[node]
            child = (node & ~1) + (v & 0x3F) * 2 + 2 + bit
            if child >= len(data) or child < tree:
                return None
            if v & (0x80 >> bit):
                acc |= data[child] << nacc
                nacc += bits
                if nacc == 8:
                    out.append(acc & 255)
                    acc = nacc = 0
                    if len(out) >= size:
                        break
                node = root
            else:
                node = child
    return bytes(out)


def blobs(lo=0x400000, hi=0xBCB000):
    if CACHE.exists():
        return pickle.loads(CACHE.read_bytes())
    r = load_clean()
    found = {}
    for o in range(lo, hi, 4):
        if r[o] not in (0x24, 0x28):
            continue
        try:
            a = _huff(r, o)
            if a and a[0] == 0x10:
                a = lz77.decompress(a, 0)
        except Exception:
            a = None
        if a:
            found[o] = a
    CACHE.write_bytes(pickle.dumps(found))
    return found


def find(tiles):
    """tiles: list of 32-byte tiles -> {blob offset: number of tiles found}"""
    out = {}
    for o, data in blobs().items():
        n = sum(1 for t in tiles if data.find(t) >= 0)
        if n:
            out[o] = n
    return out
