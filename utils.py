from struct import unpack, Struct

def magic_check(magic: bytes | str, expected: bytes | str) -> Exception | None:
    if magic != expected:
        raise ValueError(f"File magic not recognized.\nGot: {magic}\nExpected: {expected}")

def axis_convert(v):
    """
    Since Level5 games are in y-up axis, and Blender is in z-up axis, we gotta swap the y and z axis.

    >>> axis_convert((1.4, 5.8, 2.3))
    (1.4, -2.3, 5.8)
    """
    x, y, z = v
    return (x, -z, y)

def uv_convert(t):
    u, v = t
    return (u, 1.0 - v)

def triangulate(strips):
    """A generator for iterating over the faces in a set of
    strips. Degenerate triangles in strips are discarded.

    >>> triangulate([[1, 0, 1, 2, 3, 4, 5, 6]])
    [(0, 2, 1), (1, 2, 3), (2, 4, 3), (3, 4, 5), (4, 6, 5)]
    """
    triangles = []
    for strip in strips:
        if len(strip) < 3: continue # skip empty strips
        i = strip.__iter__()
        j = False
        t1, t2 = next(i), next(i)
        for k in range(2, len(strip)):
            j = not j
            t0, t1, t2 = t1, t2, next(i)
            if t0 == t1 or t1 == t2 or t2 == t0: continue
            triangles.append((t0, t1, t2) if j else (t0, t2, t1))
    return triangles

def unpack_vector(data, vector: int):
    STRUCT = Struct("<" + "f" * vector)
    return list(unpack(STRUCT.format, data[:STRUCT.size]))

def unpack_matrix(data, col, row):
    matrix = []
    for i in range(row):
        matrix.append(unpack_vector(data[(col * 3) * i:], col))
    return matrix

def read_string(data: bytes) -> str:
    return data.split(b"\x00")[0]
