"""GBA BIOS LZ77 (type 0x10) codec."""


def decompress(data: bytes, off: int = 0) -> bytes:
    if data[off] != 0x10:
        raise ValueError(f'not LZ77 at {off:#x}')
    n = int.from_bytes(data[off + 1:off + 4], 'little')
    out = bytearray()
    p = off + 4
    while len(out) < n:
        flags = data[p]
        p += 1
        for bit in range(8):
            if len(out) >= n:
                break
            if flags & (0x80 >> bit):
                x = data[p] << 8 | data[p + 1]
                p += 2
                ln, dist = (x >> 12) + 3, (x & 0xFFF) + 1
                for _ in range(ln):
                    out.append(out[-dist])
            else:
                out.append(data[p])
                p += 1
    return bytes(out)


def compress(raw: bytes) -> bytes:
    """Greedy hash-chain matcher. Distance >= 2 so output is VRAM-safe."""
    # ponytail: greedy, chain capped at 128; lazy matching if size ever matters
    n = len(raw)
    out = bytearray(b'\x10' + n.to_bytes(3, 'little'))
    chains = {}
    i = 0

    def remember(pos):
        if pos + 3 <= n:
            chains.setdefault(raw[pos:pos + 3], []).append(pos)

    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_dist = 0, 0
            if i + 3 <= n:
                cands = chains.get(raw[i:i + 3], ())
                maxlen = min(18, n - i)
                for j in reversed(cands[-128:]):
                    dist = i - j
                    if dist > 4096:
                        break
                    if dist < 2:
                        continue
                    ln = 3
                    while ln < maxlen and raw[j + ln] == raw[i + ln]:
                        ln += 1
                    if ln > best_len:
                        best_len, best_dist = ln, dist
                        if ln == maxlen:
                            break
            if best_len >= 3:
                flags |= 0x80 >> bit
                x = (best_len - 3) << 12 | (best_dist - 1)
                out += bytes((x >> 8, x & 0xFF))
                for k in range(best_len):
                    remember(i + k)
                i += best_len
            else:
                out.append(raw[i])
                remember(i)
                i += 1
        out[flag_pos] = flags
    out += b'\0' * (-len(out) % 4)
    return bytes(out)
