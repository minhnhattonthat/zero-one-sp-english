# Zero One SP — English Translation Design

## Goal
Complete English fan translation of *Zero One SP* (GBA, Fuuki 2004, `BZOJ`), built by our own reproducible toolchain. Output: `build/zero_one_sp_en.gba` + `build/zero_one_sp_en.xdelta` against the clean JP ROM.

## Decisions (from brainstorming)
- Translator: Claude, JP → English. Style: faithful, keep honorifics (-san, -kun…), JP names romanized (Asuka, Nagomu).
- Scope: everything — dialogue, UI/system strings, graphics with baked text.
- Old patch (`patch/`) is reference only: its xlsx EN lines may be reused/reviewed; its 32MB ROM diff is used only to locate hooks/graphics. No code bytes copied from it.
- Rendering: our own variable-width font (VWF) hack in Thumb asm (armips).
- ROMs live only under the project (`rom/`, `build/`), never temp dirs (mGBA temp-location dialog).

## Sub-projects (in order)
1. **Core pipeline + dialogue** — LZ77 codec, script codec, extract/insert, VWF + Latin font, build, mGBA harness, translate all script blocks.
2. **UI/system strings** — uncompressed strings, pointer tables, menus, name tags if text-rendered.
3. **Graphics** — locate (LZ77/raw 4bpp) tile text: title buttons, name-tag plates, banners; redraw in English; reinsert.

## Architecture
```
rom/  (clean JP ROM, untracked)
scripts/      python tools (stdlib + Pillow)
  lz77.py       GBA BIOS LZ77 (type 0x10) decompress/compress
  script.py     decode/encode block: header offset table + LE-u16 words; SJIS chars byte-swapped; 0x40xx control codes → {tags}
  extract.py    ROM → text/<block>.json   [{id, ctrl-prefix, jp, en}]
  insert.py     text/*.json → encoded EN blocks → LZ77 → expanded ROM area → repoint
  font.py       PNG font sheet → 1bpp/4bpp glyph table + width table
  build.py      clean ROM + asm (armips) + insert + font + graphics → build/*.gba + xdelta
asm/          armips sources (VWF hook, font table include)
text/         translation JSON (tracked; source of truth)
gfx/          edited PNGs + mapping (sub-project 3)
lua/          mGBA scripts: autoplay/screenshot, overflow logger
```
Data flow: `rom/*.gba` →(extract)→ `text/*.json` →(translate, edit `en`)→ `insert` → `build.py` → `build/*.gba` → mGBA Lua verify.

## Text encoding (observed)
- Blocks: LZ77 0x10 at ROM 0xEB0000–0xFDxxxx (~132 blocks). Decompressed = u32 offset table + script bytecode.
- Strings: u16 LE stream; char word = SJIS bytes swapped (`0x8175`=「). Controls `0x40xx` (`0x4001`=line break ｜, `0x4002`=end/wait). Other `0x40xx`/`0x00xx` = script opcodes, preserved verbatim.
- EN encoding: free code range for ASCII (e.g. single-byte-in-word `0x00xx` if unused in text context, else a reserved SJIS range) decided after renderer RE; VWF draws it.

## VWF
- Find glyph renderer (breakpoint on font ROM read via mGBA debugger/Lua; cross-check old-patch code diffs).
- Hook: for EN codes, blit proportional glyph (≤8px wide, ~10px tall to match JP line height) into the textbox tile buffer at pixel x; advance by width table. JP path untouched.
- Line capacity target ≈ 220px / ~5px avg ≈ 40+ chars, 3 lines/box.
- Font: drawn PNG (8x12 cells) → `font.py`.

## Insertion / space
- ROM expanded to 32MB; new blocks appended at 0x1000000+, pointers to each block repointed (find by scanning for `0x08xxxxxx` refs to block address).
- Line wrapping: auto-wrap EN by pixel width using the width table at insert time; explicit `{n}` honored. Overflow (>3 lines w/o page break) → insert error report, auto-split into new box only if a page-break code exists.

## Translation workflow
- Batch per block JSON; parallel subagents translate untranslated entries with shared glossary (`text/glossary.md`: names, terms, honorifics policy).
- Reuse xlsx EN where present after review.

## Testing / verification
- Unit self-checks: lz77 round-trip on every block; script decode→encode byte-identical for all blocks (before translating).
- Build check: ROM boots; Lua harness auto-advances first scenes, screenshots → inspect; overflow logger.
- Insert reports: lines exceeding width, missing translations count.

## Risks
- Renderer may compose text into OBJ/BG tiles in unusual way → VWF harder. Mitigation: old patch diff marks the hook area.
- Script blocks may be referenced by index tables not raw pointers → find table during repoint step.
- Some text may be in uncompressed regions or images (sub-projects 2/3).
