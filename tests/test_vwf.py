import unittest
import asm, font, rom
from script import _char_word


class TestVWF(unittest.TestCase):
    def test_font_tables(self):
        vmap, glyphs, widths = font.build(b'')
        self.assertEqual(len(vmap), 0x180)
        self.assertEqual(len(glyphs), 95 * 65)
        for i, c in enumerate(chr(x) for x in range(0x20, 0x7F)):
            self.assertEqual(vmap[font.glyph_index(_char_word(c))], i, c)
            self.assertTrue(1 <= widths[c] <= 7, c)
        self.assertEqual(sum(1 for b in vmap if b != 0xFF), 95)

    def test_patch(self):
        buf = bytearray(rom.load_clean()) + b'\xff' * (16 << 20)
        asm.apply(buf)
        self.assertEqual(buf[asm.HOOK:asm.HOOK + 6], bytes.fromhex('014d2847c046'))
        self.assertEqual(int.from_bytes(buf[asm.HOOK + 6:asm.HOOK + 10], 'little'), 0x08000000 + asm.CODE)
        self.assertNotEqual(buf[asm.CODE:asm.CODE + 4], b'\xff' * 4)



class TestAsmSanity(unittest.TestCase):
    def test_no_branch_to_self(self):
        """Guards against assembler bugs like `blne label` encoded as a branch to itself."""
        from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
        src = (rom.ROOT / 'asm' / 'vwf.s').read_text().replace('VWF_MAP', '0x09F00400').replace('VWF_FONT', '0x09F00600')
        code = asm.assemble(src, asm.CODE)
        for ins in Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(code, 0x08000000 + asm.CODE):
            if ins.mnemonic.startswith('b') and ins.op_str.startswith('#'):
                self.assertNotEqual(int(ins.op_str[1:], 16), ins.address, f'{ins.address:#x} {ins.mnemonic}')


if __name__ == '__main__':
    unittest.main()
