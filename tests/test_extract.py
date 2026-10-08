import unittest
from scripts import extract, rom


class TestExtract(unittest.TestCase):
    def test_extract(self):
        blocks = extract.extract_all(rom.load_clean())
        self.assertEqual(len(blocks), 132)
        entries = [e for ents in blocks.values() for e in ents]
        self.assertEqual(len(entries), 62206)
        self.assertEqual({e['form'] for e in entries}, {'dlg', 'choice'})
        # deterministic
        again = extract.extract_all(rom.load_clean())
        self.assertEqual(again, blocks)
        tm = extract.build_tm(blocks, {})
        self.assertEqual(set(tm), {e['jp'] for e in entries})
        self.assertTrue(all(v == '' for v in tm.values()))
        # existing translations survive
        k = entries[0]['jp']
        self.assertEqual(extract.build_tm(blocks, {k: 'X', 'gone': 'Y'})[k], 'X')
        self.assertNotIn('gone', extract.build_tm(blocks, {k: 'X', 'gone': 'Y'}))


if __name__ == '__main__':
    unittest.main()
