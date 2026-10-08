"""Build the translated ROM: python -m scripts.build"""
import json
import subprocess
import sys

from scripts import extract, lz77, rom
from scripts.insert import build_block

OUT = rom.ROOT / 'build' / 'zero_one_sp_en.gba'
PATCH = rom.ROOT / 'build' / 'zero_one_sp_en.xdelta'
FREE = 0x1000000            # expanded area for relocated script blocks
SIZE = 32 * 1024 * 1024


def pointer_sites(rom_bytes: bytes, targets) -> dict:
    """Aligned u32 locations (in the original 16 MiB) holding 0x08000000+target."""
    want = {0x08000000 | t: t for t in targets}
    sites = {t: [] for t in targets}
    for i, w in enumerate(memoryview(rom_bytes[:0x1000000]).cast('I')):
        if w in want:
            sites[want[w]].append(i * 4)
    return sites


def build_rom(tm: dict, opts: dict):
    clean = rom.load_clean()
    buf = bytearray(clean) + b'\xff' * (SIZE - len(clean))
    pos = FREE
    report = []
    sites = pointer_sites(clean, [rom.res_ptr(clean, i) for i in rom.SCRIPT_IDS])
    for idx in rom.SCRIPT_IDS:
        old = rom.res_ptr(clean, idx)
        raw, warns = build_block(idx, lz77.decompress(clean, old), tm, opts)
        report += warns
        comp = lz77.compress(raw)
        buf[pos:pos + len(comp)] = comp
        if not sites[old]:
            raise RuntimeError(f'no pointer to block {idx}')
        for site in sites[old]:
            buf[site:site + 4] = (0x08000000 | pos).to_bytes(4, 'little')
        pos += len(comp)
    for patch in opts.get('patches', ()):
        patch(buf)
    return bytes(buf), report


def main():
    tm = extract.load_tm()
    out, report = build_rom(tm, {})
    OUT.write_bytes(out)
    subprocess.run(['xdelta3', '-e', '-f', '-s', str(rom.CLEAN), str(OUT), str(PATCH)], check=True)
    (rom.ROOT / 'build' / 'report.txt').write_text('\n'.join(report), encoding='utf-8')
    print(f'built {OUT.name}: {len(report)} warnings')


if __name__ == '__main__':
    sys.exit(main())
