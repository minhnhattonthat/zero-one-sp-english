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


if __name__ == '__main__':
    unittest.main()
