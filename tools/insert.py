"""Turn a JP script block + translation memory into an EN block."""
import wrap
from script import NEWLINE, Block, decode_words, encode_text

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


# ops seen between two pieces of one line: waits/pauses, tag side, portrait, 0x4503 n = wait n frames
FLOW_OPS = {0x4013, 0x4005, 0x4006, 0x4007, 0x4008, 0x4009, 0x400A, 0x4050, 0x4053, 0x4054} | DIALOGUE_OPS


def continues(words: list, prev, run) -> bool:
    """run continues prev's text in the same box (prev waited with 0x4013, only flow ops in between)."""
    if prev.next != 0x4013 or run.prev not in DIALOGUE_OPS:
        return False
    gap = words[prev.end:run.start]
    i = 0
    while i < len(gap):
        if gap[i] == 0x4503:
            i += 2
        elif gap[i] in FLOW_OPS:
            i += 1
        else:
            return False
    return True


def end_state(pages, start_px, start_line):
    """(px, line) where the last page's text ends."""
    last = pages[-1]
    line = (start_line if len(pages) == 1 else 0) + len(last) - 1
    px = (start_px if len(pages) == 1 and len(last) == 1 else 0)
    return px, line, last[-1]


def build_block(idx: int, raw: bytes, tm: dict, opts: dict):
    widths = opts['widths']
    overrides = opts.get('overrides', {})
    b = Block.parse(raw)
    repl = {}
    warns = []
    carry = (0, 0)                       # (px, line) where the previous fragment stopped
    for k, run in enumerate(b.runs):
        start_px, start_line = carry if k and continues(b.words, b.runs[k - 1], run) else (0, 0)
        jp = decode_words(run.words)
        en = overrides.get(f'{idx}:{k}') or tm.get(jp)
        choice = run.prev == 0x4003
        if not en:
            pages = wrap.wrap(jp, {}, 10 ** 6, 99, start_px)       # JP: 8 px cells, explicit breaks
            px, line, last = end_state(pages, start_px, start_line)
            carry = (px + wrap.width(last, {}), line)
            continue
        where = f'{idx}:{k}'
        en = wrap.normalize(en)
        pages = wrap.wrap(en, widths, BOX_PX, 1 if choice else BOX_LINES, start_px, start_line)
        px, line, last = end_state(pages, start_px, start_line)
        carry = (px + wrap.width(last, widths), line)
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
