# Zero One SP — English translation

Fan translation of *Zero One SP* (GBA, Fuuki 2004).

## Apply the patch
Use `build/zero_one_sp_en.xdelta` with xdelta3 (or Delta Patcher) on the original ROM:
`Zero One SP (Japan).gba` (16 MiB, game code `BZOJ`). The result is a 32 MiB ROM.

## Build from source
```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
# put the clean ROM at rom/Zero One SP (Japan).gba
.venv/Scripts/python -m scripts.build          # -> build/zero_one_sp_en.gba + .xdelta, build/report.txt
.venv/Scripts/python -m unittest discover -s tests -t .
```
`xdelta3` must be on PATH.

## Layout
- `text/tm.json` — Japanese → English for every scene line; `text/overrides.json` — per-occurrence fixes (`block:run`).
- `text/ui.json`, `text/db.json`, `text/speakers.json`, `text/glossary.md` — menus, L-button database, name tags, style guide.
- `scripts/` — extract/insert/build tools; `asm/vwf.s` — variable-width font hook.
- `docs/re-notes.md` — reverse-engineering notes.

## Notes
- Debug menus and the sound test are left untranslated.
