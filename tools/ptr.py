"""Pointer repointing restricted to known pointer areas.

A whole-ROM scan for an aligned u32 equal to 0x08xxxxxx also hits compressed graphics by coincidence
(e.g. 0xD0B56C inside resource 492), so only these ranges are rewritten:
  code + rodata tables (< 0x400000), the resource table at 0x644040, the graphics table before the
  directory (0xBCA400..0xBCB0E0) and the resource directory itself."""
import rom

SAFE = [(0x0, 0x400000), (0x644040, 0x644100), (0xBCA400, 0xBCB0E0), (rom.DIR, rom.DIR + 4 * rom.DIR_COUNT)]


def sites(buf, targets) -> dict:
    """{target file offset: [site offsets]} for 0x08000000|target values in SAFE ranges."""
    want = {0x08000000 | t: t for t in targets}
    out = {t: [] for t in targets}
    for lo, hi in SAFE:
        for k, w in enumerate(memoryview(buf)[lo:hi].cast('I')):
            if w in want:
                out[want[w]].append(lo + 4 * k)
    return out


def write(buf, site, target):
    buf[site:site + 4] = (0x08000000 | target).to_bytes(4, 'little')


def repoint(buf, mapping: dict) -> dict:
    """mapping {old offset: new offset}; returns the sites found. Raises if an old target has none."""
    found = sites(bytes(buf), list(mapping))
    for old, new in mapping.items():
        if not found[old]:
            raise RuntimeError(f'no pointer to {old:#x}')
        for s in found[old]:
            write(buf, s, new)
    return found
