import struct
import unittest
from scripts import lz77, rom
from scripts.script import Block, decode_words, encode_text

R = rom.load_clean()


def raw_block(idx):
    return lz77.decompress(R, rom.res_ptr(R, idx))


class TestScript(unittest.TestCase):
    def test_identity_rebuild_all(self):
        total = 0
        for idx in rom.SCRIPT_IDS:
            raw = raw_block(idx)
            b = Block.parse(raw)
            total += len(b.runs)
            self.assertEqual(b.build({}), raw, idx)
        self.assertEqual(total, 62206)

    def test_shift_tables(self):
        raw = raw_block(880)
        b = Block.parse(raw)
        run = b.runs[0]
        new = run.words + [0x8140] * 10
        out = b.build({0: new})
        b2 = Block.parse(out)
        self.assertEqual(len(b2.runs), len(b.runs))
        self.assertEqual(b2.runs[0].words, new)
        end_byte = run.end * 2
        for old, nw in zip(b.tables, b2.tables):
            self.assertEqual(nw, old + 20 if old >= end_byte else old)
        self.assertEqual(len(out), len(raw) + 20)

    def test_text_roundtrip(self):
        ws = encode_text("Hi! It's 5:00...\nOK")
        self.assertIn(0x4001, ws)
        self.assertTrue(all(w >= 0x8140 or w == 0x4001 for w in ws))
        self.assertEqual(decode_words(ws), "Ｈｉ！　Ｉｔ’ｓ　５：００．．．\nＯＫ")

    def test_decode_jp(self):
        b = Block.parse(raw_block(752))
        self.assertTrue(any(decode_words(r.words).startswith('ゲーマー編を遊べるように') for r in b.runs))


if __name__ == '__main__':
    unittest.main()
