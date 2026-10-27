You are fixing sentence fragments in the English fan translation of the GBA visual novel "Zero One SP". Project root: H:\translation\zero-one-sp

Background: in the game, one spoken line is sometimes split into several pieces (e.g. 「この / オレに / ‥‥」) that are displayed one after another on the SAME line of the text box, with pauses in between. The translation memory stores one English text per Japanese piece, but short pieces like 「この, の, が, （ are shared by many different scenes, so their stored English fits one scene and breaks the others.

Task: review `script/batches/{F}.jsonl`. Each line is one chain: {"chain": [{"id": "block:run", "sp": speaker, "jp": piece, "en": current English}, ...]}. The pieces are shown in order and concatenated with nothing in between (so spaces must be inside the pieces).

For every chain, read the concatenated English. If it reads naturally and faithfully renders the concatenated Japanese, do nothing. Otherwise, write new English for the pieces of THAT chain so the whole reads naturally (you may move words between pieces; a piece may become a single quote mark, a space, or an empty-ish piece like " " if needed, but keep each piece non-empty). Keep quotes/brackets consistent with the glossary style: 「」 → "...", （）→ (...), 『』→ '...'. Make sure spaces between words exist exactly once at piece boundaries (put the joining space at the end of the earlier piece).

Read `glossary.md` for names/terms/style (ASCII only).

Output: write `script/batches/{F}.out.json` = one JSON object {"block:run": "new English", ...} containing ONLY the pieces you changed (every piece of a chain you rewrote should be included if its English changed). Use the Write tool. Plain ASCII only.
Validate: `.venv/Scripts/python -X utf8 -c "import sys; sys.path.insert(0, 'tools'); import json; from insert import encode_checked; from wrap import normalize; d=json.load(open('script/batches/{F}.out.json',encoding='utf-8')); [encode_checked(normalize(v),k) for k,v in d.items()]; print(len(d),'ok')"` from the project root.

Final reply: only "{F} OK n=<number of overrides>".
