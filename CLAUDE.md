# Zero One SP (GBA, Fuuki 2004, BZOJ) English translation

Skill: translate-retro-game (H:/translation/.claude/skills/translate-retro-game/SKILL.md). Read it before ROM, text or QA work.

## Commands (repo root; always `.venv/Scripts/python -X utf8 -m scripts.X`, never system python or sys.path hacks)
- Build:   `.venv/Scripts/python -X utf8 -m scripts.build` -> build/zero_one_sp_en.gba + .bps (scripts/bps.py, re-apply verified), build/report.txt (warnings)
- Check:   `.venv/Scripts/python -X utf8 -m unittest discover -s tests -t . -q` (32 tests, ~53 s; pre-commit hook runs it)
- Smoke:   `python -X utf8 H:/translation/.claude/skills/translate-retro-game/scripts/emu.py build/zero_one_sp_en.gba --out work/qa/smoke --frames 1800 --smoke` (finds tools/mgba/mGBA.exe)
- Extract: `-m scripts.extract` (scene text -> text/<idx>.json + tm.json); `-m scripts.ui extract` (refresh text/ui.json)
- Batches: `-m scripts.batches split|check bNNN|merge`; fragments `-m scripts.fragments split|merge`; overflow `-m scripts.fit list|check "text"|merge`
- Release: README patch = build/zero_one_sp_en.bps against clean 16 MiB ROM (output 32 MiB). Never publish without the user.

## Modules (scripts/)
rom: paths, resource dir 0xFD2A0C (884 LZ77 ptrs), scenes 752-883 | lz77, huff: BIOS codecs | script: scene block codec
extract/insert: JP block + TM -> EN block | wrap: pixel word-wrap | build: assemble ROM | ptr: repoint only in known tables
asm: keystone, VWF hook (asm/vwf.s) + loader patch | font/font_glyphs: VWF glyphs | ui: SJIS UI strings | db: L-menu database
tags: speaker name tags | titles: chapter title records | chapters: title cards | buttons/options/titlebg/labels: packed-gfx redraws
gfxscan: find packed gfx | dis: capstone disasm | emu + lua/harness.lua: repo mGBA harness | shots: screenshot montage
batches/fragments/fit: translation batch tooling

## Paths
- Clean ROM `rom/Zero One SP (Japan).gba` (ignored). mGBA `tools/mgba/` (ignored). Savestates `states/` (ignored). Old patch ref `patch/`.
- RE notes: `docs/re-notes.md` (encoding, text engine, VWF, mGBA gotchas, packed gfx). Design/plan: `docs/superpowers/`.
- build/ holds untracked scratch fixNN.py scripts: promote anything reusable into scripts/.

## Translation workflow
- Source of truth: `text/tm.json` (JP->EN per line), `text/overrides.json` (per occurrence `block:run`), ui/db/speakers.json.
- Batch agents: prompt `text/batches/PROMPT.md` (fragments: FPROMPT.md; dir is gitignored), then `batches check`, then `merge`.
- Freeze scripts/ (esp. wrap.py, batches.py) while batch agents run.

## Rulings (text/glossary.md is binding)
- Faithful; keep honorifics and JP name order (Mita-san, Joukouji Nagomu). Names/terms exactly as glossary tables.
- 「」->"..", （）->(..), 『』->'..', 【】->[..]; ASCII only; SFX *Slam!*; katakana-only speech -> ALL CAPS.
- Choices <= 45 chars, one line. Box = 2 lines x 224 px VWF; no manual line breaks. Debug menus/sound test stay JP.
- Gotchas: savestates hide code/VRAM changes (cold boot); scripts run uncompressed from ROM (EWRAM ~80 KB too small).

## Status
- Done: all scenes (37,115 TM lines, 0 build warnings), UI, L-menu DB, name tags, title/options/chapter graphics.
- Open bug: choice cannot be selected - states/bug_cannot_select_choice.ss0 (+ .png).
