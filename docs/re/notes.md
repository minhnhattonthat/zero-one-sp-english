# Zero One SP — reverse-engineering notes

## Data
- Resource directory: ROM 0xFD2A0C, 884 u32 pointers (LZ77 0x10). Literal ref at 0x31F34.
- Scene scripts: idx 752–883. Second pointer table to same blocks at 0x3AFB10.
- Script block: u32 `[0x10, offA, offB, offC]`, offset tables (relative to bytecode at offB), u16 bytecode.
  Text = SJIS words (stored `(b0<<8)|b1`) + `0x4001` newline after start op `4010/4011/4012` (dialogue) or `4003` (choice, ends `4004`).
  Speaker: `4056 <id>` before the line (`ffff` = none).
- UI strings: SJIS strings in ROM ~0x0FA000 referenced by literal pools (e.g. 0x16884 -> 0x080FA194). Old patch relocated these (sub-project 2).

## Text engine
- Script buffer in EWRAM at 0x02007000 (decompressed scene). Next live data seen at ~0x0201B030 / 0x0202C000 → check headroom for grown blocks.
- Interpreter/window state: 0x03003010. Dialogue window struct = same address:
  [0]=layer, [3]=tile x0 (4), [4]=tile y0 (0), [7]=width in tiles (28); col byte @+0xF3, row byte @+0xF6.
  col++ after each glyph; no auto-wrap (overflow runs into neighbouring tiles).
- SJIS→glyph index: 0x0800FC1C. `idx = (hi-0x81)*0xC0 + (lo-0x40)`; CR/LF pairs → 0x4001.
- draw_glyph(win, idx, col, row) @ 0x08010598: copies 1x2 tiles from font sheet (ROM 0x5E7F7C: u16 16 glyphs/row, u16 512 tile rows, 4bpp tiles, bg color 1)
  via 0x08002F94 to tile (win[3]+col, win[4]+2*row) of layer win[0]; then sets map via 0x080078E4.
- Layer descriptors: IWRAM 0x030020C0, 12 B each: [0]=char base, [4]=map base, [8]=tiles/row, [10]=8bpp. Layer 0 = text canvas 0x06008000 (28x5 tiles used), layer 4 = OBJ.
- Box = 2 text rows × 224 px.

## VWF (ours)
- Hook at 0x0801059A (after draw_glyph's push): `ldr r5,[pc,#4]; bx r5; nop; .word 0x09F00000`.
- ARM routine at ROM 0x1F00000 (`asm/vwf.s`): glyph idx < 0x180 with VWF_MAP[idx] != 0xFF → blit our glyph at pixel pen (clipped to win[7]*8), else original path.
- Pen state at EWRAM 0x0203FFF0: u32 last win, u8 last row, u8 pen x. Reset when win/row changes or col==0. JP glyphs set pen=(col+1)*8.
- Also sets the map entries of the cells each glyph covers via 0x080078E4(layer, win[9] palette, win[1]+col, win[2]+row*2, w, 2),
  like the original. Choices rely on it: rows get palettes 13/14 and the game swaps those palettes to move the highlight.
- Font: `tools/font_glyphs.py` (narrow, ~4.4 px avg), ink color 4, auto shadow color 2 at (+1,+1).

## mGBA scripting gotchas
- States saved with a real BIOS crash under HLE ("Jumped to invalid address 04000000"): `emu.run(..., bios=path)`.
- Choice: UP/DOWN + A selects. Dialogue advance: alternate A/B presses (each key alone stalls on some boxes).
- Load savestates with CLI `-t`, not `emu:loadStateFile` inside callbacks (game wedges).
- Set keys in `keysRead` callback. Hold A ≥6 frames; game ignores some presses (timing).
- Watchpoints miss STM/DMA; range watchpoints work for LDR/STR. Fast-forward via `-C fpsTarget=3000 -C audioSync=0 -C videoSync=0`.
- Scene text after the first box did not advance with A in tests (investigate in verification).

## Scene scripts from ROM
- Loader 0x0801DC44 normally LZ77s the scene into EWRAM 0x02007000 (only ~80 KB before data at 0x0201B000).
  Patched at 0x0801DC74 (`asm.patch_loader`) to point the interpreter (state +0x60/+0x64/+0x68) at an uncompressed copy in ROM.
- Pieces of one line: `… 4013 <flow ops> 4010 …` continue in the same box (flow ops: 4005-400A, 4050, 4053, 4054, 4503 n).

## UI strings / menus
- SJIS (normal byte order) NUL-terminated strings, referenced from code and tables below 0x400000 (e.g. hint table 0x3AF90C..0x3B00E8).
- `putc` (0x08010688) wraps when win[5] (col) >= win[7]; the VWF sets win[5] = ceil(pen/8)-1 after Latin glyphs.
- Save-slot title: `『` + chapter title + `』` + `シーン` built at 0x0802E3E0; titles were 5-byte records (idx*5), now 32-byte records.

## Packed graphics (Huffman 4-bit -> LZ77 -> container)
- Container: u32 (offset,size) x4: sheet (u16 w tiles, u16 h tiles, tiles), palette, map (u16 30, u16 20, entries).
- 0xBC62D0 title menu buttons; 0xBC117C options screen; 0xBC3114 title BG (8bpp); 0xBC1FF8 title logo animation.
- Chapter cards: 20 blobs listed at 0x3AFAC0.
- `tools/gfxscan.py` decodes every Huffman stream in 0x400000-0xBCB000 and finds which blob holds given VRAM tiles.

## Other text
- Speaker tags: raw 4bpp sheet 0x63BCC0, 60 tags x 64x16 (tag id = speaker id).
- L-menu database: three contiguous blobs at 0x62F3A4 (EVENT/PERSON/OTHERS); entry pages are story-progress variants.
  - List (0x0802F6xx): window 0x03003034 (8 tiles x 5 rows). Per row: fill(r7+0x2C, 0x8140, 9, 2, 0) = 8 fullwidth
    spaces + 0x0001, then memcpy(buf, title, strlen) and puts (0x08010900). Buffer is 24 bytes below the saved regs:
    a title over 8 words smashes the stack (issue #1, froze on hardware). EN titles: ASCII pairs padded to 8 words.
  - The VWF draws 0x8140 as an inkless VWF space, so rows never cleared: `asm.patch_db_list` hooks the fill to wipe
    the row's tiles (0x11111111) first. Verified: SELECT re-sort and tab switches redraw cleanly (mGBA).
  - Description: window 0x03003040 (15 tiles x 4 rows), puts straight from ROM. putc wraps right after a glyph
    whose pen ends past 112 px; PERSON portrait covers rows 1-2 from x=200 (88 px of text).
- UI sheet 0x6391F8 (16x21 tiles): Option/Save/Retry, PERSON/EVENT/OTHERS, "SELECT で時間順/名前順表示" labels.

## Not handled
- Pre-rendered message bitmaps near 0x627000-0x62B163 (save/load messages as images); no screen using them was found.
- Debug menus/strings (sound test, script debugger) left as is.
