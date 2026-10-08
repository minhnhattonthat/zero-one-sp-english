"""Turn a JP script block + translation memory into an EN block."""
from scripts.script import Block, decode_words, encode_text


def build_block(idx: int, raw: bytes, tm: dict, opts: dict):
    b = Block.parse(raw)
    repl = {}
    warns = []
    for k, run in enumerate(b.runs):
        en = tm.get(decode_words(run.words))
        if en:
            repl[k] = encode_text(en)
    return b.build(repl), warns
