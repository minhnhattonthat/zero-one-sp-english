import unittest
import lz77, rom


class TestLZ77(unittest.TestCase):
    def test_small(self):
        for raw in (b'', b'a', b'a' * 1000, bytes(range(256)) * 3, b'abcabcabcx'):
            c = lz77.compress(raw)
            self.assertEqual(len(c) % 4, 0)
            self.assertEqual(lz77.decompress(c), raw)

    def test_all_resources_roundtrip(self):
        r = rom.load_clean()
        for idx in range(rom.DIR_COUNT):
            raw = lz77.decompress(r, rom.res_ptr(r, idx))
            c = lz77.compress(raw)
            self.assertEqual(len(c) % 4, 0, idx)
            self.assertEqual(lz77.decompress(c), raw, idx)


if __name__ == '__main__':
    unittest.main()
