# Zero One SP — English translation

Fan translation of *Zero One SP* (GBA, Fuuki 2004).

## Apply the patch
Use `build/zero_one_sp_en.bps` with any BPS patcher (Floating IPS, Rom Patcher JS, beat) on the original ROM:
`Zero One SP (Japan).gba` (16 MiB, game code `BZOJ`, CRC32 `FD6CE886`). The result is a 32 MiB ROM.

## Build from source
```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
# put the clean ROM at rom/Zero One SP (Japan).gba
.venv/Scripts/python -m scripts.build          # -> build/zero_one_sp_en.gba + .bps, build/report.txt
.venv/Scripts/python -m unittest discover -s tests -t .
```

## Layout
- `text/tm.json` — Japanese → English for every scene line; `text/overrides.json` — per-occurrence fixes (`block:run`).
- `text/ui.json`, `text/db.json`, `text/speakers.json`, `text/glossary.md` — menus, L-button database, name tags, style guide.
- `scripts/` — extract/insert/build tools; `asm/vwf.s` — variable-width font hook.
- `docs/re-notes.md` — reverse-engineering notes.

## Notes
- Debug menus and the sound test are left untranslated.

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)
