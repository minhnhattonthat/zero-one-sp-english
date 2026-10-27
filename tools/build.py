"""Build the translated ROM: python -X utf8 tools/build.py"""
import json
import sys

import asm, bps, check_rom, ptr, buttons, chapters, db, extract, font, labels, lz77, options, rom, tags, titlebg, titles, ui
from insert import build_block

OUT = rom.ROOT / 'build' / 'zero_one_sp_en.gba'
PATCH = rom.ROOT / 'build' / 'zero_one_sp_en.bps'
FREE = 0x1000000            # expanded area for relocated script blocks
# Scene scripts are stored uncompressed and run straight from ROM (asm.patch_loader): the
# EWRAM buffer at 0x02007000 only holds ~80 KB, too small for English blocks.
# The resource directory keeps LZ77 copies for any other loader.
SIZE = 32 * 1024 * 1024




def load_overrides():
    p = rom.ROOT / 'script' / 'overrides.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def default_opts():
    return {'overrides': load_overrides(), 'widths': font.build(b'')[2], 'patches': [asm.apply, asm.patch_loader, lambda b: ui.apply(b, ui.load()), tags.apply, titles.apply, db.apply, labels.apply, buttons.apply, options.apply, chapters.apply, titlebg.apply]}


def build_rom(tm: dict, opts: dict):
    opts = {**default_opts(), **opts}
    clean = rom.load_clean()
    buf = bytearray(clean) + b'\xff' * (SIZE - len(clean))
    pos = FREE
    report = []
    sites = ptr.sites(clean, [rom.res_ptr(clean, i) for i in rom.SCRIPT_IDS])
    for idx in rom.SCRIPT_IDS:
        old = rom.res_ptr(clean, idx)
        raw, warns = build_block(idx, lz77.decompress(clean, old), tm, opts)
        report += warns
        raw_at = pos
        buf[pos:pos + len(raw)] = raw
        pos += -(-len(raw) // 4) * 4
        comp = lz77.compress(raw)
        buf[pos:pos + len(comp)] = comp
        if not sites[old]:
            raise RuntimeError(f'no pointer to block {idx}')
        dir_site = rom.DIR + 4 * idx
        for site in sites[old]:
            target = pos if site == dir_site else raw_at
            buf[site:site + 4] = (0x08000000 | target).to_bytes(4, 'little')
        pos += len(comp)
    if pos > ui.FREE:
        raise RuntimeError(f'script data overflows into the UI string area: {pos:#x}')
    for patch in opts.get('patches', ()):
        patch(buf)
    return bytes(buf), report


def main():
    check_rom.check()
    tm = extract.load_tm()
    out, report = build_rom(tm, {})
    OUT.write_bytes(out)
    clean = rom.CLEAN.read_bytes()
    p = bps.make(clean, out)
    assert bps.apply(clean, p) == out, 'patch does not reproduce the build'
    PATCH.write_bytes(p)
    (rom.ROOT / 'build' / 'report.txt').write_text('\n'.join(report), encoding='utf-8')
    print(f'built {OUT.name}: {len(report)} warnings')


if __name__ == '__main__':
    sys.exit(main())
