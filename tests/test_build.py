import unittest
from scripts import build, lz77, rom


class TestBuild(unittest.TestCase):
    def test_empty_tm_preserves_blocks(self):
        clean = rom.load_clean()
        out, report = build.build_rom({}, {})
        words = memoryview(out[:0x1000000]).cast('I')
        self.assertEqual(len(out), 32 * 1024 * 1024)
        for idx in rom.SCRIPT_IDS:
            p = rom.res_ptr(out, idx)
            self.assertGreaterEqual(p, 0x1000000)
            self.assertEqual(p % 4, 0)
            self.assertEqual(lz77.decompress(out, p), lz77.decompress(clean, rom.res_ptr(clean, idx)), idx)
            old = 0x08000000 + rom.res_ptr(clean, idx)
            self.assertNotIn(old, words, idx)   # every aligned reference repointed
        # untouched resources keep their pointers
        self.assertEqual(rom.res_ptr(out, 0), rom.res_ptr(clean, 0))


if __name__ == '__main__':
    unittest.main()
