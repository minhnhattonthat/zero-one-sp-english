import unittest
from scripts import font, insert, lz77, rom, wrap
from scripts.script import Block, decode_words

W = font.build(b'')[2]
R = rom.load_clean()


def block(idx):
    return lz77.decompress(R, rom.res_ptr(R, idx))


class TestWrap(unittest.TestCase):
    def test_fits(self):
        self.assertEqual(wrap.wrap('Hello there.', W, 224, 2), [['Hello there.']])

    def test_greedy_and_pages(self):
        text = ' '.join(['word'] * 60)
        pages = wrap.wrap(text, W, 224, 2)
        self.assertGreater(len(pages), 1)
        for p in pages:
            self.assertLessEqual(len(p), 2)
            for line in p:
                self.assertLessEqual(wrap.width(line, W), 224)
        self.assertEqual(' '.join(l for p in pages for l in p), text)

    def test_forced_newline(self):
        self.assertEqual(wrap.wrap('A\nB', W, 224, 2), [['A', 'B']])

    def test_long_word_hard_split(self):
        pages = wrap.wrap('x' * 100, W, 224, 2)
        self.assertTrue(all(wrap.width(l, W) <= 224 for p in pages for l in p))

    def test_normalize(self):
        self.assertEqual(wrap.normalize('It’s “ok”… café — yes'), 'It\'s "ok"... cafe - yes')
        with self.assertRaises(ValueError):
            insert.encode_checked('日本', 'x')


class TestInsert(unittest.TestCase):
    def test_untranslated_unchanged(self):
        raw = block(880)
        out, warns = insert.build_block(880, raw, {}, {'widths': W})
        self.assertEqual(out, raw)
        self.assertEqual(warns, [])

    def test_translation_and_split(self):
        raw = block(880)
        b = Block.parse(raw)
        jp = decode_words(b.runs[0].words)
        long = ' '.join(['sentence'] * 40)
        out, warns = insert.build_block(880, raw, {jp: long}, {'widths': W})
        b2 = Block.parse(out)
        self.assertGreater(len(b2.runs), len(b.runs))      # split into extra boxes
        self.assertIn(0x4013, b2.words[b2.runs[0].end:b2.runs[1].start])
        self.assertEqual(warns, [])

    def test_choice_overflow_warns(self):
        raw = block(752)
        b = Block.parse(raw)
        k = next(i for i, r in enumerate(b.runs) if r.prev == 0x4003)
        jp = decode_words(b.runs[k].words)
        out, warns = insert.build_block(752, raw, {jp: 'y' * 200}, {'widths': W})
        self.assertTrue(warns and '752' in warns[0])



class TestHeader(unittest.TestCase):
    def test_header_replay(self):
        from scripts.script import Run
        words = [0x4013, 0x4030, 0x4006, 0x4056, 0x23, 0x4009, 0x4050, 0x4010, 0x8175, 0x4002]
        run = Run(8, 9, [0x8175], 0x4010, 0x4002)
        self.assertEqual(insert.box_header(words, run), [0x4030, 0x4056, 0x23, 0x4009, 0x4050, 0x4010])
        words2 = [0x4030, 0x5002, 0x6010, 0x10, 0x4421, 0x4014, 0x4010, 0x8175, 0x4002]
        run2 = Run(7, 8, [0x8175], 0x4010, 0x4002)
        self.assertEqual(insert.box_header(words2, run2), [0x4030, 0x4010])
        # speaker id that happens to equal 0x4006 is kept
        words3 = [0x4030, 0x4056, 0x4006, 0x4010, 0x8175, 0x4002]
        self.assertEqual(insert.box_header(words3, Run(4, 5, [0x8175], 0x4010, 0x4002)), [0x4030, 0x4056, 0x4006, 0x4010])


if __name__ == '__main__':
    unittest.main()
