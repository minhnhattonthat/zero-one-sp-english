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


def compress(raw: bytes, bits: int = 8) -> bytes:
    """Encode raw with a canonical-ish Huffman tree in BIOS layout."""
    import heapq
    syms = []
    for c in raw:
        syms += [c & 0xF, c >> 4] if bits == 4 else [c]
    freq = {}
    for s in syms:
        freq[s] = freq.get(s, 0) + 1
    if len(freq) == 1:
        freq[(next(iter(freq)) + 1) % (1 << bits)] = 0
    heap = [(f, i, s) for i, (s, f) in enumerate(sorted(freq.items()))]
    heapq.heapify(heap)
    n = len(heap)
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        heapq.heappush(heap, (a[0] + b[0], n, (a[2], b[2])))
        n += 1
    tree = heap[0][2]
    # BIOS layout: breadth-first; each internal node's two children are stored adjacently
    table = bytearray([0])            # index 0 = root placeholder
    codes = {}
    queue = [(tree, 0, '')]            # (node, index in table, code)
    pending = []
    while queue:
        node, idx, code = queue.pop(0)
        if not isinstance(node, tuple):
            table[idx] = node
            codes[node] = code
            continue
        pos = len(table)
        if pos % 2:                    # child pairs must start on even offsets
            table.append(0)
            pos += 1
        table += b'\0\0'
        off = (pos - (idx & ~1) - 2) // 2
        if off > 0x3F:
            raise ValueError('huffman tree too wide for BIOS format')
        flags = (0x80 if not isinstance(node[0], tuple) else 0) | (0x40 if not isinstance(node[1], tuple) else 0)
        table[idx] = off | flags
        queue.append((node[0], pos, code + '0'))
        queue.append((node[1], pos + 1, code + '1'))
    if len(table) % 2 == 0:
        table.append(0)
    tree_bytes = bytes([(len(table) + 1) // 2 - 1]) + table
    tree_bytes += b'\0' * ((len(tree_bytes)) % 2)
    bitstr = ''.join(codes[s] for s in syms)
    bitstr += '0' * (-len(bitstr) % 32)
    body = b''.join(int(bitstr[i:i + 32], 2).to_bytes(4, 'little') for i in range(0, len(bitstr), 32))
    head = bytes([0x20 | bits]) + len(raw).to_bytes(3, 'little')
    out = head + tree_bytes
    out += b'\0' * (-len(out) % 4)
    return out + body
