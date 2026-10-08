"""Turn a JP script block + translation memory into an EN block."""
from scripts import wrap
from scripts.script import NEWLINE, Block, decode_words, encode_text

BOX_PX = 224
BOX_LINES = 2
DIALOGUE_OPS = {0x4010, 0x4011, 0x4012}
SPEAKER = 0x4056
# ops that are safe to replay when a line is split into extra boxes (speaker tag, tag side, portrait)
HEADER_OPS = {0x4030, SPEAKER, 0x4008, 0x4009, 0x400A, 0x4050, 0x4051, 0x4053} | DIALOGUE_OPS


def box_header(words: list, run) -> list:
    """Words that open this run's box (from the last 0x4030), replayed for continuation boxes."""
    i = run.start - 1
    while i > 0 and words[i] != 0x4030 and run.start - i < 12:
        i -= 1
    head = words[i:run.start]
    ok = words[i] == 0x4030 and all(w in HEADER_OPS or (k and head[k - 1] == SPEAKER)
                                    for k, w in enumerate(head) if w != 0x4006)
    if not ok:
        return [0x4030, run.prev]
    return [w for k, w in enumerate(head) if w != 0x4006 or (k and head[k - 1] == SPEAKER)]


def encode_checked(text: str, where: str) -> list:
    """EN text must stay within the VWF set (printable ASCII)."""
    bad = sorted({c for c in text if not ' ' <= c <= '~'})
    if bad:
        raise ValueError(f'{where}: characters outside VWF set: {bad}')
    return encode_text(text)


def build_block(idx: int, raw: bytes, tm: dict, opts: dict):
    widths = opts['widths']
    b = Block.parse(raw)
    repl = {}
    warns = []
    for k, run in enumerate(b.runs):
        en = tm.get(decode_words(run.words))
        if not en:
            continue
        where = f'{idx}:{k}'
        en = wrap.normalize(en)
        choice = run.prev == 0x4003
        pages = wrap.wrap(en, widths, BOX_PX, 1 if choice else BOX_LINES)
        splittable = run.prev in DIALOGUE_OPS and run.next == 0x4002
        if len(pages) > 1 and not splittable:
            warns.append(f'{where}: overflow ({len(pages)} pages, {"choice" if choice else "unsplittable"}): {en[:60]}')
            pages = pages[:1]
        words = []
        for p, lines in enumerate(pages):
            if p:
                words += [0x4002, 0x4013] + box_header(b.words, run)
            for n, line in enumerate(lines):
                if n:
                    words.append(NEWLINE)
                words += encode_checked(line, where)
        if not words:
            words = encode_checked(' ', where)
        repl[k] = words
    return b.build(repl), warns
