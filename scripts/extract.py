"""Extract scene script text to text/<idx>.json and keep text/tm.json in sync."""
import json

from scripts import lz77, rom
from scripts.script import Block, decode_words

TEXT = rom.ROOT / 'text'
SPEAKER_OP = 0x4056


def extract_block(raw: bytes) -> list:
    b = Block.parse(raw)
    out = []
    for k, run in enumerate(b.runs):
        speaker = None
        for i in range(run.start - 2, -1, -1):
            if b.words[i] == SPEAKER_OP:
                sp = b.words[i + 1]
                speaker = None if sp == 0xFFFF else sp
                break
        out.append({'id': k, 'speaker': speaker,
                    'form': 'choice' if run.prev == 0x4003 else 'dlg',
                    'jp': decode_words(run.words)})
    return out


def extract_all(r: bytes) -> dict:
    return {idx: extract_block(lz77.decompress(r, rom.res_ptr(r, idx))) for idx in rom.SCRIPT_IDS}


def build_tm(blocks: dict, old: dict) -> dict:
    keys = dict.fromkeys(e['jp'] for ents in blocks.values() for e in ents)
    return {k: old.get(k, '') for k in keys}


def load_tm() -> dict:
    p = TEXT / 'tm.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def save_json(path, obj):
    """One entry per line: compact and diff-friendly."""
    d = lambda x: json.dumps(x, ensure_ascii=False)
    items = [d(e) for e in obj] if isinstance(obj, list) else [f'{d(k)}: {d(v)}' for k, v in obj.items()]
    o, c = ('[', ']') if isinstance(obj, list) else ('{', '}')
    path.write_text(o + '\n' + ',\n'.join(items) + '\n' + c + '\n', encoding='utf-8')


def main():
    TEXT.mkdir(exist_ok=True)
    blocks = extract_all(rom.load_clean())
    for idx, ents in blocks.items():
        save_json(TEXT / f'{idx}.json', ents)
    tm = build_tm(blocks, load_tm())
    save_json(TEXT / 'tm.json', tm)
    print(f'{len(blocks)} blocks, {sum(map(len, blocks.values()))} runs, {len(tm)} unique, '
          f'{sum(1 for v in tm.values() if v)} translated')


if __name__ == '__main__':
    main()
