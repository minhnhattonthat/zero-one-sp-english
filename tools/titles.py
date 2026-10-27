"""Chapter titles: originally 20 fixed 5-byte SJIS records at ROM 0xFA29C indexed as idx*5 (code at
0x0802E408). We patch the multiply to idx*32 and point the literal at a new table of 32-byte records."""
import ui

LITERAL = 0x2E47C            # code literal pointing to the title table
MUL = 0x2E40A                # lsls r2, r3, #2 ; adds r2, r2, r1   (r2 = idx * 5)
TABLE = 0x1E80000
STRIDE = 32
TITLES = ['Nightmare', 'Assassin', 'Flight', 'Escape', 'Turn', 'Atrocity', 'Progress', 'Undying', 'Mad Dog',
          'Recapture', 'Revenge', 'Rampage', 'Transfer', 'Showdown', 'Aftermath', 'Missing', 'Mind', 'Destruction',
          'Conclusion', 'Rebirth']


def apply(buf: bytearray):
    assert buf[MUL:MUL + 4] == bytes.fromhex('9a005218'), 'unexpected title code'
    assert int.from_bytes(buf[LITERAL:LITERAL + 4], 'little') == 0x080FA29C
    for i, t in enumerate(TITLES):
        data = ui.encode(t) + b'\0'
        assert len(data) <= STRIDE
        buf[TABLE + i * STRIDE:TABLE + (i + 1) * STRIDE] = data.ljust(STRIDE, b'\0')
    buf[MUL:MUL + 4] = bytes.fromhex('5a01c046')          # lsls r2, r3, #5 ; nop
    buf[LITERAL:LITERAL + 4] = (0x08000000 | TABLE).to_bytes(4, 'little')
