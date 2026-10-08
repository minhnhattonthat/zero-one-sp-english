@ Variable-width font hook for draw_glyph (0x08010598).
@ Entered from the hook at 0x0801059A (Thumb -> ARM via bx) after the original
@ prologue `push {r4,r5,r7,lr}`.  r0=win r1=glyph index r2=col r3=row.
@ win: [0]=layer [3]=tile x0 [4]=tile y0.  Layer descriptors at 0x030020C0 (12 B):
@ [0]=char base, [8]=tiles per row, [10]=8bpp flag.
@ Glyphs listed in VWF_MAP draw at a pixel pen; others take the original path.
.arm
vwf_entry:
    cmp   r1, #0x180
    bhs   jp_path
    ldr   r5, lit_map
    ldrb  r5, [r5, r1]
    cmp   r5, #0xff
    beq   jp_path
    push  {r0-r3, r6, r8-r11}
    ldr   r6, lit_state
    ldr   r4, [r6]
    ldrb  r7, [r6, #4]
    cmp   r4, r0
    bne   reset
    cmp   r7, r3
    bne   reset
    cmp   r2, #0
    beq   reset
    ldrb  r4, [r6, #5]
    b     have_pen
reset:
    mov   r4, r2, lsl #3
    str   r0, [r6]
    strb  r3, [r6, #4]
have_pen:
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
    bne   advance                     @ 8bpp layer: skip drawing
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
advance:
    pop   {r8}
    add   r4, r4, r8
    ldr   r6, lit_state
    strb  r4, [r6, #5]
    pop   {r0-r3, r6, r8-r11}
    pop   {r4, r5, r7, lr}            @ draw_glyph epilogue
    bx    lr

jp_path:
    ldr   r5, lit_state               @ JP glyph: pen = (col + 1) * 8
    str   r0, [r5]
    strb  r3, [r5, #4]
    add   r4, r2, #1
    mov   r4, r4, lsl #3
    strb  r4, [r5, #5]
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
