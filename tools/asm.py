"""Assemble asm/vwf.s with keystone and patch the draw_glyph hook."""
from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_THUMB, Ks

import font
from rom import ROOT

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


DB_LIST = 0x2F728           # L-menu list, per row: fill(buf, 0x8140, 9, 2, 0) = 8 fullwidth spaces + end
DB_BLANK = CODE + 0x2000


def patch_db_list(buf: bytearray):
    """Clear each list row's tiles before it is drawn. The JP glyphs overwrote whole cells; the VWF only
    adds ink and draws the fullwidth space as nothing, so re-sorted, scrolled or emptied rows kept the
    old title. Fills the row (2 tile rows x win[7], color 1 like a JP blank) then runs the original fill.
    r7 = frame: [r7+0x24] window, [r7+2] row."""
    assert buf[DB_LIST:DB_LIST + 18] == bytes.fromhex('381c2c302a490022009209220223e2f70dfe'), \
        'unexpected L-menu list bytes'
    code = assemble('''
        push {r4-r6, lr}
        ldr  r0, [r7, #0x24]
        ldrb r1, [r0]
        lsls r2, r1, #1
        adds r1, r1, r2
        lsls r1, r1, #2
        ldr  r2, desc
        adds r1, r1, r2
        ldr  r4, [r1]
        ldrb r5, [r1, #8]
        ldrb r2, [r0, #4]
        ldrh r3, [r7, #2]
        lsls r3, r3, #1
        adds r2, r2, r3
        muls r2, r5, r2
        ldrb r3, [r0, #3]
        adds r2, r2, r3
        lsls r2, r2, #5
        adds r4, r4, r2
        ldrb r6, [r0, #7]
        subs r5, r5, r6
        lsls r5, r5, #5
        lsls r6, r6, #3
        ldr  r3, blank
        movs r1, #2
    rows:
        adds r2, r6, #0
    words:
        stmia r4!, {r3}
        subs r2, #1
        bne  words
        adds r4, r4, r5
        subs r1, #1
        bne  rows
        sub  sp, #4
        adds r0, r7, #0
        adds r0, #0x2c
        ldr  r1, space
        movs r2, #0
        str  r2, [sp]
        movs r2, #9
        movs r3, #2
        ldr  r4, fill
        bl   call_r4
        add  sp, #4
        pop  {r4-r6}
        pop  {r0}
        bx   r0
    call_r4:
        bx   r4
        .align 2
    desc:  .word 0x030020C0
    blank: .word 0x11111111
    space: .word 0x00008140
    fill:  .word 0x08012355
    ''', DB_BLANK, thumb=True)
    buf[DB_BLANK:DB_BLANK + len(code)] = code
    # ldr r3,lit; bl veneer; b back; veneer: bx r3; nop; lit; nop
    hook = assemble('''
        ldr  r3, [pc, #8]
        bl   0x0802f730
        b    0x0802f73a
        bx   r3
        nop
    ''', DB_LIST, thumb=True) + (0x08000001 + DB_BLANK).to_bytes(4, 'little') + bytes.fromhex('c046')
    assert len(hook) == 18
    buf[DB_LIST:DB_LIST + 18] = hook
