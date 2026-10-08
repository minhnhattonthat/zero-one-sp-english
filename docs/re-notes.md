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
- Font: `scripts/font_glyphs.py` (narrow, ~4.4 px avg), ink color 4, auto shadow color 2 at (+1,+1).

## mGBA scripting gotchas
- Load savestates with CLI `-t`, not `emu:loadStateFile` inside callbacks (game wedges).
- Set keys in `keysRead` callback. Hold A ≥6 frames; game ignores some presses (timing).
- Watchpoints miss STM/DMA; range watchpoints work for LDR/STR. Fast-forward via `-C fpsTarget=3000 -C audioSync=0 -C videoSync=0`.
- Scene text after the first box did not advance with A in tests (investigate in verification).
