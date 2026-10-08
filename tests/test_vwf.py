import unittest
from scripts import asm, font, rom
from scripts.script import _char_word


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


if __name__ == '__main__':
    unittest.main()
