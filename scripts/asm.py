"""Assemble asm/vwf.s with keystone and patch the draw_glyph hook."""
from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_THUMB, Ks

from scripts import font
from scripts.rom import ROOT

CODE = 0x1F00000            # ROM offset of the VWF routine
MAP = CODE + 0x400
FONT = CODE + 0x600
HOOK = 0x1059A              # inside draw_glyph, after its push


def assemble(src: str, addr: int, thumb=False) -> bytes:
    enc, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB if thumb else KS_MODE_ARM).asm(src, 0x08000000 + addr)
    return bytes(enc)


LOADER = 0x1DC74            # scene loader, right after r1 = scene block pointer


def patch_loader(buf: bytearray):
    """Skip LZ77 into the 0x02007000 buffer; point the interpreter at the (uncompressed) block itself.
    Original: decompress(r1, 0x02007000); state+0x68 = buf+0x10; state+0x64 = state+0x60 = buf+[buf+8]."""
    assert buf[LOADER:LOADER + 2] == bytes.fromhex('0d4a'), 'unexpected loader bytes'
    code = assemble('''
        adds r3, r1, #0
        ldr  r0, [pc, #0x38]
        adds r2, r3, #0
        adds r2, #0x10
        str  r2, [r0, #0x68]
        ldr  r2, [r3, #8]
        adds r2, r2, r3
        str  r2, [r0, #0x64]
        str  r2, [r0, #0x60]
        b    0x0801dc9e
    ''', LOADER, thumb=True)
    assert int.from_bytes(buf[0x1DCB0:0x1DCB4], 'little') == 0x03003010
    buf[LOADER:LOADER + len(code)] = code


def apply(buf: bytearray):
    vmap, glyphs, _ = font.build(bytes(buf))
    src = (ROOT / 'asm' / 'vwf.s').read_text()
    src = src.replace('VWF_MAP', hex(0x08000000 + MAP)).replace('VWF_FONT', hex(0x08000000 + FONT))
    code = assemble(src, CODE)
    assert len(code) <= MAP - CODE, len(code)
    buf[CODE:CODE + len(code)] = code
    buf[MAP:MAP + len(vmap)] = vmap
    buf[FONT:FONT + len(glyphs)] = glyphs
    # ldr r5,[pc,#4]; bx r5; nop; .word vwf_entry (ARM)
    hook = bytes.fromhex('014d2847c046') + (0x08000000 + CODE).to_bytes(4, 'little')
    assert buf[HOOK:HOOK + 10] == bytes.fromhex('89b004af3860 0c1c111c'.replace(' ', '')), 'unexpected bytes at hook'
    buf[HOOK:HOOK + 10] = hook
