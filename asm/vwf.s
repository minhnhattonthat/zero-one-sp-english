@ Variable-width font hook for draw_glyph (0x08010598).
@ Entered from the hook at 0x0801059A (Thumb -> ARM via bx) after the original
@ prologue `push {r4,r5,r7,lr}`.  r0=win r1=glyph index r2=col r3=row.
@ win: [0]=layer [3]=tile x0 [4]=tile y0 [5]=putc col [7]=width in tiles.
@ Layer descriptors at 0x030020C0 (12 B): [0]=char base, [8]=tiles per row, [10]=8bpp flag.
@ Glyph sources:
@   index < 0x180 with VWF_MAP[index] != 0xFF  -> one glyph (fullwidth Latin)
@   index >= 0x9EE0 -> ASCII pair: code = index - 0x7EC0 = (c1 << 8) | c2, two glyphs
@                      (UI strings pack two ASCII chars per 2-byte code; c2 = 0x7F is padding)
@ Everything else takes the original path.
@ Pen state at 0x0203FFF0: u32 window, u8 row, u8 pen x, u8 last col.
.arm
vwf_entry:
    ldr   r5, lit_pairlo
    cmp   r1, r5
    bhs   pair
    cmp   r1, #0x180
    bhs   jp_path
    ldr   r5, lit_map
    ldrb  r5, [r5, r1]
    cmp   r5, #0xff
    beq   jp_path
    mov   r4, #0xff                   @ no second glyph
    b     vwf
pair:
    sub   r5, r1, #0x7E00
    sub   r5, r5, #0xC0               @ code = (c1 << 8) | c2
    and   r4, r5, #0xff
    mov   r5, r5, lsr #8
    sub   r5, r5, #0x20               @ first glyph
    cmp   r4, #0x7f
    moveq r4, #0xff
    subne r4, r4, #0x20               @ second glyph or none
vwf:
    push  {r0-r3, r6, r8-r11}
    push  {r4}                        @ second glyph
    ldr   r6, lit_state
    ldr   r4, [r6]
    ldrb  r7, [r6, #4]
    cmp   r4, r0
    bne   reset
    cmp   r7, r3
    bne   reset
    cmp   r2, #0
    beq   reset
    ldrb  r4, [r6, #5]                @ continue only if col is the expected next one:
    ldrb  r7, [r6, #6]                @ last col + 1 (scene text) or ceil(pen/8) (putc)
    add   r7, r7, #1
    cmp   r2, r7
    beq   have_pen
    add   r7, r4, #7
    cmp   r2, r7, lsr #3
    beq   have_pen
reset:
    mov   r4, r2, lsl #3
    str   r0, [r6]
    strb  r3, [r6, #4]
have_pen:
    push  {r4}                        @ start pen
    bl    blit
    ldr   r5, [sp, #4]
    cmp   r5, #0xff
    beq   one_glyph                   @ (keystone mis-assembles conditional bl to a label)
    bl    blit
one_glyph:
    pop   {r5}                        @ start pen
    add   sp, sp, #4
    bl    mark
    ldr   r6, lit_state
    strb  r4, [r6, #5]
    ldr   r5, [sp, #8]                @ col argument
    strb  r5, [r6, #6]
    pop   {r0-r3, r6, r8-r11}
    add   r12, r4, #7                 @ putc wraps when win[5] (col) >= win[7]: make col
    mov   r12, r12, lsr #3            @ follow the pixel pen, ceil(pen/8) - 1 (putc adds 1)
    sub   r12, r12, #1
    strb  r12, [r0, #5]
    pop   {r4, r5, r7, lr}            @ draw_glyph epilogue
    bx    lr

@ blit: draw glyph r5 at pixel pen r4 on row r3 of window r0; r4 += advance.
@ Clobbers r1, r2, r5-r12.
blit:
    push  {r0, r3, lr}
    ldr   r7, lit_font
    add   r5, r5, r5, lsl #6          @ glyph * 65
    add   r7, r7, r5
    ldrb  r8, [r7], #1                @ advance width; r7 -> 16 rows x 4 bytes
    push  {r8}
    ldrb  r12, [r0, #7]               @ clip to window width (tiles)
    rsb   r12, r4, r12, lsl #3
    cmp   r12, r8
    movlt r8, r12
    ldrb  r9, [r0]
    add   r9, r9, r9, lsl #1
    ldr   r10, lit_desc
    add   r9, r10, r9, lsl #2         @ layer descriptor
    ldrb  r10, [r9, #10]
    cmp   r10, #0
    bne   blit_done                   @ 8bpp layer: skip drawing
    ldr   r10, [r9]                   @ char base
    ldrb  r11, [r9, #8]               @ tiles per row
    ldrb  r5, [r0, #3]                @ tile x0
    ldrb  r9, [r0, #4]
    add   r9, r9, r3, lsl #1          @ tile y of this text row
    mov   r1, #0                      @ y
yloop:
    mov   r2, #0                      @ x
xloop:
    cmp   r2, r8
    bge   xdone
    ldrb  r12, [r7, r2, lsr #1]
    tst   r2, #1
    movne r12, r12, lsr #4
    ands  r12, r12, #0xf
    beq   xnext
    add   r3, r4, r2                  @ px
    add   r0, r9, r1, lsr #3          @ tile y
    mul   r0, r11, r0
    add   r0, r0, r5
    add   r0, r0, r3, lsr #3          @ tile index
    add   r0, r10, r0, lsl #5
    and   lr, r1, #7
    add   r0, r0, lr, lsl #2
    and   lr, r3, #7
    add   r0, r0, lr, lsr #1
    bic   r0, r0, #1
    and   lr, r3, #3
    mov   lr, lr, lsl #2              @ nibble shift within halfword
    ldrh  r3, [r0]
    mov   r6, #0xf
    bic   r3, r3, r6, lsl lr
    orr   r3, r3, r12, lsl lr
    strh  r3, [r0]
xnext:
    add   r2, r2, #1
    b     xloop
xdone:
    add   r7, r7, #4
    add   r1, r1, #1
    cmp   r1, #16
    blo   yloop
blit_done:
    pop   {r8}
    add   r4, r4, r8
    pop   {r0, r3, lr}
    bx    lr

@ mark: set the map entries (palette win[9]) of the cells covered by pen r5..r4 on row r3 of window r0,
@ as the original draw_glyph does per glyph; choice highlighting works through these palettes.
mark:
    push  {r0-r4, lr}
    ldrb  r12, [r0, #7]               @ width in tiles
    mov   r1, r5, lsr #3              @ first cell
    sub   r2, r4, #1
    mov   r2, r2, lsr #3              @ last cell
    cmp   r2, r12
    subge r2, r12, #1
    subs  r2, r2, r1
    blt   mark_done
    add   r2, r2, #1                  @ cell count
    sub   sp, sp, #8
    str   r2, [sp]                    @ w
    mov   r12, #2
    str   r12, [sp, #4]               @ h
    ldrb  r12, [r0, #1]
    add   r2, r12, r1                 @ map x
    ldrb  r12, [r0, #2]
    add   r3, r12, r3, lsl #1         @ map y
    ldrb  r1, [r0, #9]                @ palette
    ldrb  r0, [r0]                    @ layer
    ldr   r12, lit_mapset
    mov   lr, pc
    bx    r12
    add   sp, sp, #8
mark_done:
    pop   {r0-r4, lr}
    bx    lr

jp_path:
    ldr   r5, lit_state               @ JP glyph: pen = (col + 1) * 8
    str   r0, [r5]
    strb  r3, [r5, #4]
    add   r4, r2, #1
    mov   r4, r4, lsl #3
    strb  r4, [r5, #5]
    strb  r2, [r5, #6]
    sub   sp, sp, #0x24               @ replaced instructions
    add   r7, sp, #0x10
    str   r0, [r7]
    mov   r4, r1
    mov   r1, r2
    ldr   r5, lit_resume
    bx    r5

lit_map:    .word VWF_MAP
lit_font:   .word VWF_FONT
lit_state:  .word 0x0203FFF0
lit_desc:   .word 0x030020C0
lit_resume: .word 0x080105A5
lit_pairlo: .word 0x00009EE0
lit_mapset: .word 0x080078E5          @ Thumb: (layer, pal, x, y, [sp]=w, [sp+4]=h)
