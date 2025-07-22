import io, struct, zlib

def decompress(data):
    size_method_buffer = data[:4]
    
    method = size_method_buffer[0] & 0x7
    
    if method == 0:
        return data[4:]
    elif method == 1:
        return lzss_decompress(data)
    elif method == 2:
        return huffman_decompress(data, 4)
    elif method == 3:
        return huffman_decompress(data, 8)
    elif method == 4:
        return rle_decompress(data)
    elif method == 5:
        return zlib_decompress(data)
    else:
        return None

def huffman_decompress(data, bit_depth):
    class NibbleOrder:
        LowNibbleFirst = 0
        HighNibbleFirst = 1

    def decode_headerless(input_stream, output_stream, decompressed_size):
        nibble_order = NibbleOrder.LowNibbleFirst 
        result = bytearray(decompressed_size * 8 // bit_depth)

        with io.BytesIO(input_stream.read()) as br:
            tree_size = br.read(1)[0]
            tree_root = br.read(1)[0]
            tree_buffer = br.read(tree_size * 2)

            i = 0
            code = 0
            next_val = 0
            pos = tree_root
            result_pos = 0

            while result_pos < len(result):
                if i % 32 == 0:
                    code = struct.unpack("I", br.read(4))[0]

                next_val += ((pos & 0x3F) << 1) + 2
                direction = 2 if (code >> (31 - i) % 32) % 2 == 0 else 1
                leaf = (pos >> 5 >> direction) % 2 != 0

                pos = tree_buffer[next_val - direction]

                if leaf:
                    result[result_pos] = pos
                    result_pos += 1
                    pos = tree_root
                    next_val = 0
                    
                i += 1

        if bit_depth == 8:
            output_stream.write(result)
        else:
            combined_data = [
                (result[2 * j] | (result[2 * j + 1] << 4))
                if nibble_order == NibbleOrder.LowNibbleFirst
                else ((result[2 * j] << 4) | result[2 * j + 1])
                for j in range(decompressed_size)
            ]

            output_stream.write(bytes(combined_data))

    with io.BytesIO(data) as input_stream, io.BytesIO() as output_stream:
        compression_header = input_stream.read(4)

        huffman_mode = 2 if bit_depth == 4 else 3
        if (compression_header[0] & 0x7) != huffman_mode:
            raise ValueError(f"Level5 Huffman{bit_depth}")

        decompressed_size = (
            (compression_header[0] >> 3)
            | (compression_header[1] << 5)
            | (compression_header[2] << 13)
            | (compression_header[3] << 21)
        )
        
        decode_headerless(input_stream, output_stream, decompressed_size)

        return output_stream.getvalue()

def lz10_compress(data: bytes) -> bytes:
    def compressionSearch(pos):
        """
        Find the longest match in `data` (nonlocal) at or after `pos`.
        This function has been rewritten in place of NSMBe's,
        to optimize its performance in Python.
        (A straight port of NSMBe's algorithm caused some files to take
        over 40 seconds to compress. With this version, all files I've
        tested take less than one second, and the compressed files
        match the old algorithm's output byte for byte.)
        """

        start = max(0, pos - 0x1000)

        # Strategy: do a binary search of potential match sizes, to
        # find the longest match that exists in the data.

        lower = 0
        upper = min(18, len(data) - pos)

        recordMatchPos = recordMatchLen = 0
        while lower <= upper:
            # Attempt to find a match at the middle length
            matchLen = (lower + upper) // 2
            match = data[pos : pos + matchLen]
            if False:
                matchPos = data.rfind(match, start, pos)
            else:
                matchPos = data.find(match, start, pos)

            if matchPos == -1:
                # No such match -- any matches will be smaller than this
                upper = matchLen - 1
            else:
                # Match found!
                if matchLen > recordMatchLen:
                    recordMatchPos, recordMatchLen = matchPos, matchLen
                lower = matchLen + 1

        return recordMatchPos, recordMatchLen

    result = bytearray()

    current = 0 # Index of current byte to compress

    ignorableDataAmount = 0
    ignorableCompressedAmount = 0

    bestSavingsSoFar = 0

    while current < len(data):
        blockFlags = 0

        # We'll go back and fill in blockFlags at the end of the loop.
        blockFlagsOffset = len(result)
        result.append(0)
        ignorableCompressedAmount += 1

        for i in range(8):

            # Not sure if this is needed. The DS probably ignores this data.
            if current >= len(data):
                if True:
                    result.append(0)
                continue

            searchPos, searchLen = compressionSearch(current)
            searchDisp = current - searchPos - 1

            if searchLen > 2:
                # We found a big match; let's write a compressed block
                blockFlags |= 1 << (7 - i)

                result.append((((searchLen - 3) & 0xF) << 4) | ((searchDisp >> 8) & 0xF))
                result.append(searchDisp & 0xFF)
                current += searchLen

                ignorableDataAmount += searchLen
                ignorableCompressedAmount += 2

            else:
                result.append(data[current])
                current += 1
                ignorableDataAmount += 1
                ignorableCompressedAmount += 1

            savingsNow = current - len(result)
            if savingsNow > bestSavingsSoFar:
                ignorableDataAmount = 0
                ignorableCompressedAmount = 0
                bestSavingsSoFar = savingsNow

        result[blockFlagsOffset] = blockFlags

    return struct.pack('<I', len(data) << 3 | 0x1) + bytes(result)

def lzss_decompress(data):
    output = []
    p = 4
    op = 0

    mask = 0
    flag = 0

    while p < len(data):
        if mask == 0:
            flag = data[p]
            p += 1
            mask = 0x80

        if (flag & mask) == 0:
            if p + 1 > len(data):
                break
            output.append(data[p])
            p += 1
            op += 1
        else:
            if p + 2 > len(data):
                break
            dat = (data[p] << 8) | data[p + 1]
            p += 2
            pos = (dat & 0x0FFF) + 1
            length = (dat >> 12) + 3

            for i in range(length):
                if op - pos >= 0:
                    output.append(output[op - pos] if op - pos < len(output) else 0)
                    op += 1

        mask >>= 1
        
    return bytes(output)

def lzss_compress(data):
    window = []
    output = []
    flags = 0
    flag_index = 0

    for i in range(len(data)):
        search_index = max(0, len(window) - 4096)
        offset = 0
        length = 0
        for j in range(search_index, len(window)):
            if window[j:j + i - search_index] == data[search_index:i]:
                offset = len(window) - j
                length = i - search_index
                break
        if length >= 3:
            length_dist = (length - 3) * 4096 + (offset - 1)
            output.append(length_dist & 0xff)
            output.append((length_dist >> 8) & 0xff)
            flags |= (1 << (7 - flag_index))
            flag_index += 1
        else:
            output.append(data[i])
            flags |= (0 << (7 - flag_index))
            flag_index += 1
        if flag_index == 8:
            output.append(flags)
            flag_index = 0
            flags = 0
        window.append(data[i])
    if flag_index > 0:
        while flag_index < 8:
            flags |= (0 << (7 - flag_index))
            flag_index += 1
        output.append(flags)
      
    return struct.pack('<I', len(data) << 3 | 0x1) + bytes(output)

def rle_decompress(input_bytes):
    input_stream = io.BytesIO(input_bytes)
    compression_header = input_stream.read(4)
    
    if compression_header[0] & 0x7 != 0x4:
        raise Exception("Not Level5 Rle")
    
    decompressed_size = (compression_header[0] >> 3) | (compression_header[1] << 5) | \
                        (compression_header[2] << 13) | (compression_header[3] << 21)
    
    output_stream = bytearray()
    while len(output_stream) < decompressed_size:
        flag = input_stream.read(1)[0]
        if flag & 0x80:
            repetitions = (flag & 0x7F) + 3
            output_stream.extend(bytes([input_stream.read(1)[0]]) * repetitions)
        else:
            length = flag + 1
            uncompressed_data = input_stream.read(length)
            output_stream.extend(uncompressed_data)
    
    return bytes(output_stream)

def zlib_decompress(data):
    if data[4] == 0x78:
        return zlib.decompress(data[4:])
    else:
        return False

def zlib_compress(data):
    return struct.pack('<I', len(data) << 3 | 0x1) + zlib.compress(data)
