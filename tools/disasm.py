"""Disassemble ROM: python -X utf8 tools/disasm.py <addr hex> <len> [arm] [rom path]"""
import sys

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs

from rom import CLEAN


def dis(data, addr, n, arm=False, base=0x08000000):
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM if arm else CS_MODE_THUMB)
    off = addr - base if addr >= base else addr
    for ins in md.disasm(data[off:off + n], base + off):
        print(f'{ins.address:08x}: {ins.bytes.hex():10} {ins.mnemonic} {ins.op_str}')


if __name__ == '__main__':
    a = sys.argv
    rom = open(a[4] if len(a) > 4 else CLEAN, 'rb').read()
    dis(rom, int(a[1], 16), int(a[2], 0), len(a) > 3 and a[3] == 'arm')
