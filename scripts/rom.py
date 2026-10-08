import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / 'rom' / 'Zero One SP (Japan).gba'
DIR = 0xFD2A0C          # resource directory: 884 u32 pointers, all LZ77
DIR_COUNT = 884
SCRIPT_IDS = range(752, 884)


def load_clean() -> bytes:
    return CLEAN.read_bytes()


def res_ptr(rom: bytes, idx: int) -> int:
    """File offset of resource idx."""
    return struct.unpack_from('<I', rom, DIR + 4 * idx)[0] - 0x08000000
