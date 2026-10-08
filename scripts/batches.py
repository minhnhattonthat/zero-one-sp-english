"""Translation batches.

  python -m scripts.batches split [JP_CHARS]   write text/batches/bNNN.jsonl for untranslated lines (story order)
  python -m scripts.batches check bNNN         validate text/batches/bNNN.out.json
  python -m scripts.batches merge              fold all *.out.json into text/tm.json

Batch line: {"k": key, "sp": speaker, "form": "dlg"|"choice", "jp": text}  (k = index into tm.json keys)
Context line: {"ctx": true, "sp": ..., "jp": ..., "en": ...}  (already translated, for continuity)
Output: bNNN.out.json = {"<k>": "English", ...} covering every k in the batch.
"""
import json
import sys

from scripts import extract, rom
from scripts.insert import encode_checked
from scripts.wrap import normalize

TEXT = rom.ROOT / 'text'
DIR = TEXT / 'batches'


def speakers():
    return json.loads((TEXT / 'speakers.json').read_text(encoding='utf-8'))


def split(limit=9000):
    tm = extract.load_tm()
    keys = {k: i for i, k in enumerate(tm)}
    names = speakers()
    DIR.mkdir(exist_ok=True)
    for f in DIR.glob('b*.jsonl'):
        f.unlink()
    batches, cur, size, queued = [], [], 0, set()
    for idx in rom.SCRIPT_IDS:
        for e in json.loads((TEXT / f'{idx}.json').read_text(encoding='utf-8')):
            sp = names.get(str(e['speaker'])) if e['speaker'] is not None else None
            jp = e['jp']
            if tm[jp] or jp in queued:
                cur.append({'ctx': True, 'sp': sp, 'jp': jp, 'en': tm[jp] or None})
                continue
            queued.add(jp)
            cur.append({'k': keys[jp], 'sp': sp, 'form': e['form'], 'jp': jp})
            size += len(jp)
            if size >= limit:
                batches.append(cur)
                cur, size = [], 0
    if any('k' in x for x in cur):
        batches.append(cur)
    for n, b in enumerate(batches):
        # trim leading context to the last 8 lines before the first todo line
        first = next(i for i, x in enumerate(b) if 'k' in x)
        b = b[max(0, first - 8):]
        lines = [json.dumps(x, ensure_ascii=False) for x in b]
        (DIR / f'b{n:03d}.jsonl').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'{len(batches)} batches, {len(queued)} lines')


def load_batch(name):
    return [json.loads(l) for l in (DIR / f'{name}.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]


def check(name) -> list:
    """-> list of problems (empty = ok)."""
    todo = {str(x['k']): x for x in load_batch(name) if 'k' in x}
    p = DIR / f'{name}.out.json'
    if not p.exists():
        return [f'{p.name} missing']
    out = json.loads(p.read_text(encoding='utf-8'))
    probs = [f'missing k={k}' for k in todo if not str(out.get(k, '')).strip()]
    probs += [f'unknown k={k}' for k in out if k not in todo]
    for k, en in out.items():
        try:
            encode_checked(normalize(en), f'k={k}')
        except ValueError as e:
            probs.append(str(e))
        if k in todo and todo[k]['form'] == 'choice' and len(en) > 45:
            probs.append(f'k={k}: choice longer than 45 chars')
    return probs


def merge():
    tm = extract.load_tm()
    keys = list(tm)
    n = 0
    for p in sorted(DIR.glob('b*.out.json')):
        name = p.name.split('.')[0]
        probs = check(name)
        if probs:
            print(f'{name}: {len(probs)} problems, skipped: {probs[:3]}')
            continue
        for k, en in json.loads(p.read_text(encoding='utf-8')).items():
            tm[keys[int(k)]] = normalize(en)
            n += 1
    extract.save_json(TEXT / 'tm.json', tm)
    print(f'merged {n}; translated {sum(1 for v in tm.values() if v)}/{len(tm)}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'split':
        split(int(sys.argv[2]) if len(sys.argv) > 2 else 9000)
    elif cmd == 'check':
        probs = check(sys.argv[2])
        print('\n'.join(probs) or 'OK')
        sys.exit(1 if probs else 0)
    elif cmd == 'merge':
        merge()
