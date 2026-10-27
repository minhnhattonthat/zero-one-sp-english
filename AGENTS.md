# Zero One SP (GBA, Fuuki 2004, BZOJ) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root; always `.venv/Scripts/python -X utf8`, never system python)
- Build:    `.venv/Scripts/python -X utf8 tools/build.py` -> build/zero_one_sp_en.gba + .bps (tools/bps.py, re-apply verified), build/report.txt (warnings); checks the dump against `rom.sha1` first
- Check:    `.venv/Scripts/python -X utf8 tools/check.py` (unittest, 32 tests, ~53 s; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/zero_one_sp_en.gba --out work/qa/smoke --frames 1800 --smoke` (finds tools/mgba/mGBA.exe)
- Extract:  `tools/extract.py` (scene text -> script/<idx>.json + tm.json); `tools/ui.py extract` (refresh script/ui.json)
- Batches:  `tools/batches.py split|check bNNN|merge`; fragments `tools/fragments.py split|merge`; overflow `tools/fit.py list|check "text"|merge`
- Release:  README patch = build/zero_one_sp_en.bps against the clean 16 MiB ROM (output 32 MiB). Never publish without the user.
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Modules (tools/, flat scripts: `import rom`; tests put tools/ on sys.path in tests/__init__.py)
rom: paths, resource dir 0xFD2A0C (884 LZ77 ptrs), scenes 752-883 | lz77, huff: BIOS codecs | script: scene block codec
extract/insert: JP block + TM -> EN block | wrap: pixel word-wrap | build: assemble ROM | ptr: repoint only in known tables
asm: keystone, VWF hook (asm/vwf.s) + loader patch | font/font_glyphs: VWF glyphs | ui: SJIS UI strings | db: L-menu database
tags: speaker name tags | titles: chapter title records | chapters: title cards | buttons/options/titlebg/labels: packed-gfx redraws
gfxscan: find packed gfx | disasm: capstone disasm | emu + tools/lua/harness.lua: repo mGBA harness | shots: screenshot montage
batches/fragments/fit: translation batch tooling | check_rom: dump SHA-1 gate | check: one-command check

## Paths
- Original ROM: `rom/Zero One SP (Japan).gba` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: mGBA in `tools/mgba/` (gitignored). Savestates: `work/states/`. Old patch ref: `patch/` (gitignored).
- Text: `script/` (`tm.json` JP->EN per line, `overrides.json` per occurrence `block:run`, `ui.json`, `db.json`, `speakers.json`, `<idx>.json` extracted scenes; batches in `script/batches/`, gitignored). Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`. Design/plan: `docs/superpowers/`.
- Briefs: `docs/translator-brief.md` (bNNN), `docs/fragment-brief.md` (fNNN).
- build/ holds untracked scratch fixNN.py scripts: promote anything reusable into tools/.

## Rulings
- Edit source files (.py .lua .s .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- `glossary.md` is binding: faithful; keep honorifics and JP name order (Mita-san, Joukouji Nagomu); names/terms exactly as its tables.
- 「」->"..", （）->(..), 『』->'..', 【】->[..]; ASCII only; SFX *Slam!*; katakana-only speech -> ALL CAPS.
- Choices <= 45 chars, one line. Box = 2 lines x 224 px VWF; no manual line breaks. Debug menus/sound test stay JP.
- Freeze tools/ (esp. wrap.py, batches.py) while batch agents run.
- Gotchas: savestates hide code/VRAM changes (cold boot); scripts run uncompressed from ROM (EWRAM ~80 KB too small); never name a tools/ module after a stdlib one (dis.py shadowed `dis`, hence disasm.py).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
