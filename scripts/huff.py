"""GBA BIOS Huffman (types 0x24 = 4-bit, 0x28 = 8-bit) codec."""


def decompress(data: bytes, off: int = 0) -> bytes:
    bits = data[off] & 0x0F
    size = int.from_bytes(data[off + 1:off + 4], 'little')
    tree = off + 4
    tree_size = (data[tree] + 1) * 2
    root = tree + 1
    p = tree + tree_size
    out = bytearray()
    acc, nacc = 0, 0
    node, is_data = root, False
    while len(out) < size:
        word = int.from_bytes(data[p:p + 4], 'little')
        p += 4
        for b in range(31, -1, -1):
            bit = (word >> b) & 1
            v = data[node]
            child = (node & ~1) + (v & 0x3F) * 2 + 2 + bit
            leaf = v & (0x80 >> bit)
            if leaf:
                sym = data[child]
                acc |= sym << nacc
                nacc += bits
                if nacc == 8:
                    out.append(acc & 0xFF)
                    acc, nacc = 0, 0
                    if len(out) >= size:
                        break
                node = root
            else:
                node = child
    return bytes(out[:size])


def compress(raw: bytes) -> bytes:
    """4-bit BIOS Huffman (type 0x24). With <= 16 symbols every child offset fits in 6 bits.

    Layout: tree[0] = size byte, root at tree[1]; a node at table index i (absolute tree+1+i) has its
    child pair at index ((i + 1) & ~1) + 2 * offset + 1, so pairs start at odd indices."""
    import heapq
    syms = [n for c in raw for n in (c & 0xF, c >> 4)]
    freq = {}
    for s_ in syms:
        freq[s_] = freq.get(s_, 0) + 1
    if len(freq) == 1:
        freq[(next(iter(freq)) + 1) & 0xF] = 0
    heap = [(f, i, s_) for i, (s_, f) in enumerate(sorted(freq.items()))]
    heapq.heapify(heap)
    n = len(heap)
    while len(heap) > 1:
        a, b = heapq.heappop(heap), heapq.heappop(heap)
        heapq.heappush(heap, (a[0] + b[0], n, (a[2], b[2])))
        n += 1
    table = [0]
    codes = {}
    queue = [(heap[0][2], 0, '')]
    while queue:
        node, idx, code = queue.pop(0)
        if not isinstance(node, tuple):
            table[idx] = node
            codes[node] = code
            continue
        pos = len(table)
        if pos % 2 == 0:
            table.append(0)
            pos += 1
        table += [0, 0]
        off = (pos - 1 - ((idx + 1) & ~1)) // 2
        assert 0 <= off <= 0x3F
        table[idx] = off | (0x80 if not isinstance(node[0], tuple) else 0) | (0x40 if not isinstance(node[1], tuple) else 0)
        queue.append((node[0], pos, code + '0'))
        queue.append((node[1], pos + 1, code + '1'))
    while (1 + len(table)) % 4:
        table.append(0)
    tree = bytes([(1 + len(table)) // 2 - 1] + table)
    bitstr = ''.join(codes[s_] for s_ in syms)
    bitstr += '0' * (-len(bitstr) % 32)
    body = b''.join(int(bitstr[i:i + 32], 2).to_bytes(4, 'little') for i in range(0, len(bitstr), 32))
    return bytes([0x24]) + len(raw).to_bytes(3, 'little') + tree + body
