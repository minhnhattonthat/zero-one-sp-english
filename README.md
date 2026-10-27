# Zero One SP English translation

Unofficial English fan translation of **Zero One SP** (GBA, Fuuki, 2004): the source text and tools that build the
patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English (`tm.json`, `overrides.json`, `ui.json`, `db.json`, `speakers.json`). Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, build, batch tooling. |
| `asm/` | Variable-width font hook. |
| `tests/` | unittest suite (needs the ROM). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/zero-one-sp-english
cd zero-one-sp-english
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
# copy your dump to: rom/Zero One SP (Japan).gba
#   (16,777,216 bytes, SHA-1 7ed2b25dff8783a924c5d6dfe2add95d766f32f0; the build refuses any other dump, see rom.sha1)
.venv/Scripts/python -X utf8 tools/build.py             # -> build/zero_one_sp_en.gba + .bps (32 MiB output)
.venv/Scripts/python -X utf8 tools/check.py             # tests
```

Debug menus and the sound test are left untranslated.

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Fuuki's and is included only so the
translation can be checked against it. Zero One SP is (c) Fuuki; this project is not affiliated with them. Do not
share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
