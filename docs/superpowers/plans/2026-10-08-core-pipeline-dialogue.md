# Core Pipeline + Dialogue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `build/zero_one_sp_en.gba` (+ xdelta) from the clean JP ROM with all 132 scene scripts translated to English and rendered by our own VWF.

**Architecture:** Python tools in `scripts/` decompress the 132 LZ77 scene blocks, split them into text runs + opaque bytecode, extract runs to `text/<idx>.json`, and on build re-encode English as fullwidth SJIS, wrap by pixel width, rebuild blocks (shifting header offset tables), recompress, append to expanded ROM and repoint. A Thumb VWF routine (assembled with keystone) hooks the glyph renderer so fullwidth Latin codes draw proportionally.

**Tech Stack:** Python 3.12 stdlib, Pillow, keystone-engine 0.9.2, capstone 5.0.3 (in `.venv`), xdelta3 (scoop), mGBA 0.11-dev Lua scripting (`tools/mgba/mGBA.exe --script`).

**Spec:** `docs/superpowers/specs/2026-10-08-zero-one-sp-translation-design.md`

## Global Constraints

- Clean ROM: `rom/Zero One SP (Japan).gba` (16 MiB, header `BZOJ`). Never modified.
- ROMs/outputs only under project dirs (`rom/`, `build/`); never in temp (mGBA temp-location dialog).
- Resource directory at ROM 0xFD2A0C, 884 entries; scene scripts are idx 752–883.
- EN text encoded as fullwidth SJIS (`ord(c)-0x20+0xFF00` mapped through cp932); word stored LE u16 with value `(b0<<8)|b1`.
- Translation: faithful, keep honorifics, JP name order, romanized names (glossary in `text/glossary.md`).
- No code bytes copied from the old patch; it is a map only.
- Tests are plain `python -I -m unittest` in `tests/`; no frameworks.

## Review Focus

- Untranslated entry (`en` empty) → original JP bytes emitted unchanged (game must still run mid-translation). Test in Task 4.
- EN char not representable in fullwidth SJIS (e.g. `é`, smart quotes `’`) → normalized (`'`, `"`, `...`) or build error naming block/id, never silent garbage. Test in Task 4.
- Run longer than box capacity in a non-splittable context → build report lists it; build still completes. Test in Task 4.
- Relocated compressed blocks must be 4-byte aligned (BIOS LZ77 reads) and every old pointer replaced in both tables. Test in Task 5.
- Duplicate JP strings (e.g. 「あめんぼ…」×716) translated once via `text/tm.json`, stays consistent. Test in Task 3.

---

### Task 1: Environment + LZ77 codec

**Files:** Create `requirements.txt`, `scripts/lz77.py`, `tests/test_lz77.py`, `scripts/rom.py`.

**Interfaces — Produces:**
- `lz77.decompress(data: bytes, off: int = 0) -> bytes`
- `lz77.compress(raw: bytes) -> bytes` (type 0x10, VRAM-safe: displacement ≥ 2, padded to 4 bytes)
- `rom.load_clean() -> bytes`, `rom.DIR = 0xFD2A0C`, `rom.SCRIPT_IDS = range(752, 884)`, `rom.res_ptr(rom: bytes, idx) -> int` (file offset)

- [ ] Step 1: `python -m venv .venv && .venv/Scripts/python -m pip install pillow capstone==5.0.3 keystone-engine==0.9.2`; `requirements.txt` lists them. `.venv/` added to `.gitignore`.
- [ ] Step 2: test — for every one of 884 resources: `decompress(compress(decompress(rom, p))) == decompress(rom, p)`, and compressed length % 4 == 0; and a unit case `compress(b'')`/`compress(b'a'*1000)` round-trips.
- [ ] Step 3: implement (hash-chain greedy matcher over window 4096, max len 18).
- [ ] Step 4: run `python -I -m unittest tests.test_lz77` → PASS. Commit.

### Task 2: Script block codec

**Files:** Create `scripts/script.py`, `tests/test_script.py`.

**Interfaces — Produces:**
- `Block.parse(raw: bytes) -> Block` with `.header` (4 u32), `.tables` (list of u32 offsets, all tables incl. offC), `.words: list[int]` (bytecode), `.runs: list[Run]`
- `Run(start: int, end: int, words: list[int], prev: int, next: int)` — word indices into bytecode; text word = `w >= 0x8140 or w == 0x4001`; a run must be preceded by one of `{0x4010,0x4011,0x4012,0x4003,0x4001}`… (start set measured in Step 1).
- `Block.build(replacements: dict[int, list[int]]) -> bytes` — run index → new words (may include split sequences); shifts every table offset `o` by sum of deltas of runs ending at or before `o` (byte offsets = 2×word index).
- `decode_words(ws) -> str` (`0x4001`→`\n`), `encode_text(s) -> list[int]`.

- [ ] Step 1: measure exact preceding-word set & check no table offset falls strictly inside a run (assert across 132 blocks).
- [ ] Step 2: tests: (a) `Block.parse(raw).build({}) == raw` for all 132 blocks; (b) replace run 0 of block 880 with 10 extra words → every table entry > run end shifts by 20 bytes, entries before unchanged, reparse finds same run count; (c) `decode_words(encode_text("Hi!\nOK")) == "Ｈｉ！\nＯＫ"`-equivalent round trip.
- [ ] Step 3: implement; Step 4: tests PASS; commit.

### Task 3: Extraction + translation memory

**Files:** Create `scripts/extract.py`, `tests/test_extract.py`; output `text/<idx>.json`, `text/tm.json`.

**Interfaces — Produces:**
- `text/<idx>.json`: `[{"id": int (run index), "speaker": int|null (operand after nearest preceding 0x4056), "form": "dlg"|"nar"|"other", "jp": str}]`
- `text/tm.json`: `{jp: en}` translation memory — the single source of EN strings (dedups 58.8k runs → 36.7k).

- [ ] Step 1: test: extraction is deterministic; total runs == sum of `len(Block.runs)`; `tm.json` keys == set of all jp.
- [ ] Step 2: implement; run; commit `text/`.

### Task 4: Insertion + wrapping

**Files:** Create `scripts/insert.py`, `scripts/wrap.py`, `tests/test_insert.py`.

**Interfaces:**
- Consumes `Block`, `tm.json`, font width table `asm/font_widths.bin`-equivalent `font.widths: dict[str,int]`.
- `wrap.wrap(text: str, widths, max_px: int, max_lines: int) -> list[list[str]]` pages of lines.
- `insert.build_block(idx, raw, tm, widths) -> (bytes, list[str] warnings)`

- [ ] Step 1: tests: empty/missing EN → JP words unchanged; `’`→`'`, `…`→`...`, `é`→`e`; unencodable char → `ValueError` naming idx/id; long text in `dlg` form splits with `0x4002,0x4013,0x4030,<orig start op>`; long text in non-splittable form → warning, text truncated to fit.
- [ ] Step 2: implement; Step 3: PASS; commit.

### Task 5: ROM build

**Files:** Create `scripts/build.py`, `tests/test_build.py`.

- [ ] Step 1: build = copy clean ROM → pad to 32 MiB with 0xFF → for each script idx: build block, compress, append 4-aligned at ≥0x1000000 → replace every aligned u32 == old `0x08000000+p` with new pointer → apply asm patches (Task 7) → write `build/zero_one_sp_en.gba` → `xdelta3 -e -f -s rom build/... build/zero_one_sp_en.xdelta`.
- [ ] Step 2: test: build with empty TM → every directory entry decompresses to original block bytes; each block pointer replaced in both tables (0xFD2A0C dir and 0x3AFB10 table).
- [ ] Step 3: boot test via `lua/autoplay.lua` (Task 6) → screenshot shows JP dialogue unchanged. Commit.

### Task 6: mGBA harness + renderer RE

**Files:** Create `lua/autoplay.lua`, `lua/watch.lua`, `scripts/shots.py` (montage), `docs/re-notes.md`.

- [ ] Step 1: `autoplay.lua`: env-free config at top (out dir, frames, keys); taps A every N frames, screenshot every M frames; savestate at frame F. Run with `timeout 90 tools/mgba/mGBA.exe --script lua/autoplay.lua build/<rom>`.
- [ ] Step 2: RE: in dialogue, dump VRAM/BG regs (`emu:read16(0x04000008..)`) to find text layer + tile base; set write watchpoint on a text tile → log PC; disassemble with capstone around PC; follow back to the per-char routine (expect near old-patch hook sites 0x16884/0x1A060/0x1AF38/0x2760C); find font base (SJIS→glyph index function), glyph size/bpp, pen-x variable.
- [ ] Step 3: write `docs/re-notes.md`: routine addresses, register usage, glyph format, tile layout, line height, box px width/lines. Commit.

### Task 7: VWF + Latin font

**Files:** Create `gfx/font_en.png` (drawn programmatically from a pixel font definition in `scripts/font.py`), `scripts/font.py`, `asm/vwf.s`, `scripts/asm.py`.

- [ ] Step 1: `font.py`: glyphs for ASCII 0x20–0x7E, height = JP line height, width per glyph stored; emit glyph bytes in the game's glyph format + width table.
- [ ] Step 2: `asm.py`: keystone Thumb assemble `asm/vwf.s` at a fixed address in free space (0x1F00000), patch hook (BL/LDR-BX trampoline) at the renderer site from re-notes.
- [ ] Step 3: VWF logic: if char word in fullwidth Latin range → look up our glyph + width, OR glyph bits into tile buffer at pen_x (crossing tile boundary), pen_x += width; else original path with pen_x += JP width (keep pen_x in pixels).
- [ ] Step 4: test: TM override for first scene line = "The quick brown fox jumps over the lazy dog. 0123456789!?" → autoplay screenshot shows proportional text, no garbage. Commit.

### Task 8: Translate

**Files:** Create `text/glossary.md`, `scripts/batches.py`; fill `text/tm.json`.

- [ ] Step 1: glossary: characters (from speaker ids + xlsx names), recurring terms, honorific policy.
- [ ] Step 2: `batches.py split N` writes `text/batches/bNNN.json` of untranslated jp in story order with context (speaker, neighbors); `batches.py merge` folds `en` back into `tm.json`, validating every jp key matched and no empty strings.
- [ ] Step 3: translate batches with parallel subagents (each gets glossary + batch path, writes `en` fields), merge, build, spot-check screenshots.
- [ ] Step 4: commit text.

### Task 9: Verification

- [ ] Build report: 0 errors, list of truncation warnings → fix by shortening EN in TM, rebuild until 0.
- [ ] Autoplay through first scenes on each arc; screenshot montage reviewed.
- [ ] Final commit + xdelta in `build/`.
