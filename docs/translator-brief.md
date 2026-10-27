You are translating the Japanese GBA visual novel "Zero One SP" (Fuuki, 2004; SF adventure about psychic powers, the "Gamer", the "Creator", investigations; protagonist Joukouji Nagomu) into English. Project root: H:\translation\zero-one-sp

Task: translate batch `script/batches/{B}.jsonl` and write `script/batches/{B}.out.json`.

1. Read `glossary.md` fully first. Its style rules and name/term tables are binding (faithful translation, keep honorifics, 「」→"...", （）→(...), 『』→'...', 【】→[...], ASCII only, choices <= 45 chars, sound effects as *Slam!*).
2. Read the batch file. Each line is JSON:
   - {"k": N, "sp": speaker-or-null, "form": "dlg"|"choice", "jp": "..."} → translate. sp = name on the speaker tag (null = narration/system). "\n" inside jp is only the original manual line break: ignore it, never put line breaks in English.
   - {"ctx": true, ...} → context only, do not output.
   Lines are in story order; use neighbours for context. Some lines are fragments of one sentence split by in-game effects (a line that is only 「, or a sentence continuing in the next line): translate pieces so they read naturally in sequence.
3. Write `script/batches/{B}.out.json`: one JSON object mapping every k (as string) to its English. Use the Write tool. Plain ASCII only (straight quotes, "..." for ellipses, - for dashes).
4. Validate from the project root: `.venv/Scripts/python -X utf8 tools/batches.py check {B}`. Fix every problem and re-run until it prints OK.
5. If you had to decide a recurring name/term not in the glossary, append one line per decision to `script/batches/{B}.notes.txt` as `JP => EN`. Do not edit glossary.md.

Quality bar: natural, faithful English a fan-translation reader enjoys; preserve character voice; don't skip or summarize; adapt wordplay when literal would be meaningless (no translator notes). Be concise where possible (aim <= ~95 chars per line; longer is fine when the Japanese is long).

Final reply: only "{B} OK" (or the problem). Notes go only in the notes file. Do not paste the translation.
