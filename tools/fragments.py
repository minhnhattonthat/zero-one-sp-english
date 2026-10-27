"""Fragment chains: runs that continue the previous run in the same box (insert.continues).
Short JP pieces like 「この are shared by many chains, so one TM entry can't fit all of them.

  python -X utf8 tools/fragments.py split   write script/batches/fNNN.jsonl review batches (chains with shared pieces)
  python -X utf8 tools/fragments.py merge   fold fNNN.out.json ({"idx:k": en}) into script/overrides.json
"""
import collections
import json
import sys

import extract, lz77, rom
from batches import DIR, speakers
from insert import continues, encode_checked
from script import Block, decode_words
from wrap import normalize

OVR = rom.ROOT / 'script' / 'overrides.json'


def chains(r: bytes):
    """-> list of chains; chain = [(idx, k, jp, speaker), ...] with len >= 2."""
    out = []
    for idx in rom.SCRIPT_IDS:
        b = Block.parse(lz77.decompress(r, rom.res_ptr(r, idx)))
        ents = json.loads((extract.TEXT / f'{idx}.json').read_text(encoding='utf-8'))
        cur = []
        for k, run in enumerate(b.runs):
            item = (idx, k, decode_words(run.words), ents[k]['speaker'])
            if cur and continues(b.words, b.runs[k - 1], run):
                cur.append(item)
            else:
                if len(cur) > 1:
                    out.append(cur)
                cur = [item]
        if len(cur) > 1:
            out.append(cur)
    return out


def at_risk(all_chains):
    use = collections.Counter(jp for ch in all_chains for _, _, jp, _ in ch)
    occ = collections.Counter()
    for idx in rom.SCRIPT_IDS:
        for e in json.loads((extract.TEXT / f'{idx}.json').read_text(encoding='utf-8')):
            occ[e['jp']] += 1
    return [ch for ch in all_chains if any(occ[jp] > 1 for _, _, jp, _ in ch)]


def split(per=120):
    tm = extract.load_tm()
    names = speakers()
    risky = at_risk(chains(rom.load_clean()))
    for f in DIR.glob('f*.jsonl'):
        f.unlink()
    for n in range(0, len(risky), per):
        lines = []
        for ch in risky[n:n + per]:
            lines.append(json.dumps({'chain': [
                {'id': f'{i}:{k}', 'sp': names.get(str(sp)) if sp is not None else None, 'jp': jp, 'en': tm.get(jp, '')}
                for i, k, jp, sp in ch]}, ensure_ascii=False))
        (DIR / f'f{n // per:03d}.jsonl').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(risky)} risky chains -> {(len(risky) + per - 1) // per} batches')


def merge():
    ovr = json.loads(OVR.read_text(encoding='utf-8')) if OVR.exists() else {}
    live = {f'{i}:{k}' for ch in chains(rom.load_clean()) for i, k, _, _ in ch}
    for p in sorted(DIR.glob('f*.out.json')):
        data = json.loads(p.read_text(encoding='utf-8'))
        for key, en in data.items():
            if key not in live:          # no longer a fragment under the current continuation rule
                continue
            encode_checked(normalize(en), key)
            ovr[key] = normalize(en)
    extract.save_json(OVR, dict(sorted(ovr.items())))
    print(f'{len(ovr)} overrides')


if __name__ == '__main__':
    {'split': split, 'merge': merge}[sys.argv[1]]()
