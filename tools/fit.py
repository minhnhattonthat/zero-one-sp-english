"""Lines that overflow their box in a non-splittable context (from build/report.txt).

  python -X utf8 tools/fit.py list            write script/batches/fit.jsonl
  python -X utf8 tools/fit.py check "text"    print lines/pages the text needs (must be 1 page)
  python -X utf8 tools/fit.py merge           fold fit.out.json into script/overrides.json
"""
import json
import sys

import extract, font, rom
from batches import DIR, speakers
from fragments import OVR
from insert import BOX_LINES, BOX_PX
from wrap import normalize, wrap


def pages(text):
    return wrap(normalize(text), font.build(b'')[2], BOX_PX, BOX_LINES)


def listing():
    ovr = json.loads(OVR.read_text(encoding='utf-8')) if OVR.exists() else {}
    tm = extract.load_tm()
    names = speakers()
    out = []
    for line in (rom.ROOT / 'build' / 'report.txt').read_text(encoding='utf-8').splitlines():
        key = line.split(': ')[0]
        idx, k = map(int, key.split(':'))
        e = json.loads((extract.TEXT / f'{idx}.json').read_text(encoding='utf-8'))[k]
        sp = names.get(str(e['speaker'])) if e['speaker'] is not None else None
        out.append(json.dumps({'id': key, 'sp': sp, 'jp': e['jp'], 'en': ovr.get(key) or tm[e['jp']]}, ensure_ascii=False))
    (DIR / 'fit.jsonl').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(len(out), 'lines')


def merge():
    ovr = json.loads(OVR.read_text(encoding='utf-8')) if OVR.exists() else {}
    for k, v in json.loads((DIR / 'fit.out.json').read_text(encoding='utf-8')).items():
        if len(pages(v)) != 1:
            raise SystemExit(f'{k} still too long: {v}')
        ovr[k] = normalize(v)
    extract.save_json(OVR, dict(sorted(ovr.items())))
    print(len(ovr), 'overrides')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'list':
        listing()
    elif cmd == 'check':
        p = pages(sys.argv[2])
        print(f'{len(p)} page(s):', p)
    elif cmd == 'merge':
        merge()
