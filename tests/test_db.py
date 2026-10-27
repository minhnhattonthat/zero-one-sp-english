import unittest
import db, rom


class TestDB(unittest.TestCase):
    def test_roundtrip_identity(self):
        r = rom.load_clean()
        for blob in db.blobs(r):
            rebuilt = db.build_blob(blob['titles'], blob['pages'], blob['order'])
            again = db.parse(rebuilt, 0)
            for k in ('titles', 'pages', 'order'):
                self.assertEqual(again[k], blob[k])
            self.assertEqual(again['size'], len(rebuilt))

    def test_apply_relocates(self):
        buf = bytearray(rom.load_clean()) + b'\xff' * (16 << 20)
        ents = db.extract(bytes(buf))
        ents[0]['title_en'] = 'Cyborg Case'
        ents[0]['desc_en'] = ['A cyborg made by Rude.']
        db.apply(buf, ents)
        new = db.parse(bytes(buf), db.NEW)
        self.assertEqual(new['titles'][0], db.encode_title('Cyborg Case'))
        self.assertEqual(new['pages'][0][0], db.encode_page('A cyborg made by Rude.'))
        self.assertEqual(len(new['pages'][1]), len(db.blobs(rom.load_clean())[0]['pages'][1]))
        self.assertNotIn(0x08000000 | db.BASE, memoryview(bytes(buf[:0x1000000])).cast('I'))

    def test_page_too_long(self):
        with self.assertRaises(ValueError):
            db.encode_page('word ' * 60)

    def test_title_fits_game_buffer(self):
        """Issue #1: the list copies a title over 8 words on the stack; longer titles crash on hardware."""
        ws = db.encode_title('Sekiguchi Shin')
        self.assertEqual(ws[:2], [ord('S') << 8 | ord('e'), ord('k') << 8 | ord('i')])
        self.assertEqual(len(ws), db.TITLE_CELLS)
        self.assertEqual(db.encode_title('Shin')[2:], [0x7F7F] * 6)
        with self.assertRaises(ValueError):
            db.encode_title('Mysterious Young Man')

    def test_portrait_rows(self):
        text = 'My classmate. A friend who is great at every sport. Nickname: Shin-chan.'
        self.assertGreater(len(db.page_lines(text, db.PERSON)), len(db.page_lines(text, 0)) - 1)
        self.assertTrue(all(db.width(l, db._widths()) <= db.PORTRAIT_PX for l in db.page_lines(text, db.PERSON)[:2]))


if __name__ == '__main__':
    unittest.main()
