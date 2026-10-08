import unittest
from scripts import build, lz77, rom


class TestBuild(unittest.TestCase):
    def test_empty_tm_preserves_blocks(self):
        clean = rom.load_clean()
        out, report = build.build_rom({}, {'overrides': {}})
        words = memoryview(out[:0x1000000]).cast('I')
        self.assertEqual(len(out), 32 * 1024 * 1024)
        for idx in rom.SCRIPT_IDS:
            p = rom.res_ptr(out, idx)
            self.assertGreaterEqual(p, 0x1000000)
            self.assertEqual(p % 4, 0)
            self.assertEqual(lz77.decompress(out, p), lz77.decompress(clean, rom.res_ptr(clean, idx)), idx)
            old = 0x08000000 + rom.res_ptr(clean, idx)
            self.assertNotIn(old, words, idx)   # every aligned reference repointed
        # scene table points at uncompressed copies (loader patched to run scripts from ROM)
        for k in range(10):
            ptr = int.from_bytes(out[0x3AFB10 + 4 * k:0x3AFB14 + 4 * k], 'little') - 0x08000000
            self.assertGreaterEqual(ptr, 0x1000000)
            self.assertEqual(out[ptr:ptr + 4], bytes([0x10, 0, 0, 0]))
        self.assertEqual(out[0x1DC74:0x1DC76], bytes.fromhex('0b1c'))   # adds r3, r1, #0
        # untouched resources keep their pointers
        self.assertEqual(rom.res_ptr(out, 0), rom.res_ptr(clean, 0))



class TestUI(unittest.TestCase):
    def test_ui_relocation(self):
        from scripts import ui
        clean = bytearray(rom.load_clean()) + b'\xff' * (16 << 20)
        ents = ui.extract(bytes(clean))
        ents[0]['en'] = 'End'
        ui.apply(clean, ents[:1])
        old = int(ents[0]['addr'], 16) | 0x08000000
        self.assertNotIn(old, memoryview(bytes(clean[:0x1000000])).cast('I'))
        self.assertEqual(clean[ui.FREE:ui.FREE + 7], bytes.fromhex('8264828e828400'))



class TestIntegrity(unittest.TestCase):
    """Repointing must only touch pointer tables, never data inside other resources."""

    @classmethod
    def setUpClass(cls):
        cls.clean = rom.load_clean()
        cls.out, _ = build.build_rom({}, {})

    def test_other_resources_intact(self):
        for idx in range(rom.DIR_COUNT):
            if idx in rom.SCRIPT_IDS:
                continue
            self.assertEqual(lz77.decompress(self.out, rom.res_ptr(self.out, idx)),
                             lz77.decompress(self.clean, rom.res_ptr(self.clean, idx)), idx)

    def test_db_blobs_repointed(self):
        from scripts import db
        table = memoryview(self.out[0x644040:0x644080]).cast('I')
        for old in (0x0862F3A4, 0x08632EFC, 0x08635D0C):
            self.assertNotIn(old, table)



class TestPairEncoding(unittest.TestCase):
    def test_ui_pairs(self):
        from scripts import ui
        self.assertEqual(ui.encode('Yes'), b'Ye' + b's\x7f')
        self.assertEqual(ui.encode('Hi\n\nOK{01}'), b'Hi\n\nOK\x01')
        self.assertEqual(ui.encode('{}'), b'')

    def test_save_title_fits(self):
        """『title』　シーンNN　HH：MM：SS{01} must stay within the game's 40-byte buffers."""
        from scripts import titles, ui
        parts = {e['addr']: ui.encode(e['en']) for e in ui.load() if e['addr'] in ('0xfbf60', '0xfbf64', '0xfbf6c', '0xfbf74', '0xfbe40')}
        fixed = 4 + len(parts['0xfbf74']) + 6 * 2 + 2 * len(parts['0xfbe40']) + 1   # NN, gap, 6 digits, 2 colons, {01}
        for t in titles.TITLES:
            total = len(parts['0xfbf60']) + len(ui.encode(t)) + len(parts['0xfbf64']) + len(parts['0xfbf6c']) + fixed
            self.assertLessEqual(total + 1, 40, t)


if __name__ == '__main__':
    unittest.main()
