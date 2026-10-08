import unittest
from scripts import db, rom


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
        ents[0]['title_en'] = 'Cyborg Incident'
        ents[0]['desc_en'] = ['A cyborg made by Rude.']
        db.apply(buf, ents)
        new = db.parse(bytes(buf), db.NEW)
        self.assertEqual(new['titles'][0], db.encode_page('Cyborg Incident'))
        self.assertEqual(new['pages'][0][0], db.encode_page('A cyborg made by Rude.'))
        self.assertEqual(len(new['pages'][1]), len(db.blobs(rom.load_clean())[0]['pages'][1]))
        self.assertNotIn(0x08000000 | db.BASE, memoryview(bytes(buf[:0x1000000])).cast('I'))

    def test_page_too_long(self):
        with self.assertRaises(ValueError):
            db.encode_page('word ' * 60)


if __name__ == '__main__':
    unittest.main()
