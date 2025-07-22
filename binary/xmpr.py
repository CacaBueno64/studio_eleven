from ..utils import *
from .compression import decompress

from struct import pack, unpack, unpack_from, Struct

class XMPR:
    MAGIC = b"XMPR"
    STRUCT = Struct("<4s I II II II II II II II")
    def __init__(self, data=None):
        self.XPRM: XPRM
        self.Proprieties: XMPR_Proprieties
        self.NodeTable = []
        self.PrimitiveName = b""
        self.MaterialName = b""
        
        if data:
            self.read(data)
    
    def read(self, data):
        xmpr_magic, \
        xprm_offset, xprm_lenght, \
        properties_offset, \
        unk_offset, unk_length, unk1_offset, unk1_length, unk2_offset, unk2_length, \
        nodes_offset, nodes_lenght, \
        mesh_name_offset, mesh_name_lenght,\
        material_name_offset, material_name_length = \
            unpack_from(XMPR.STRUCT.format, data)
        
        magic_check(xmpr_magic, XMPR.MAGIC)
        if unk_length or unk1_length or unk2_length: print(f"UNK SECTION FOUND")
        
        self.XPRM = XPRM(data[xprm_offset : xprm_offset + xprm_lenght])
        self.Proprieties = XMPR_Proprieties(data[properties_offset : properties_offset + XMPR_Proprieties.STRUCT.size])
        self.PrimitiveName = data[mesh_name_offset     : mesh_name_offset     + mesh_name_lenght    ]
        self.MaterialName  = data[material_name_offset : material_name_offset + material_name_length]
        self.NodeTable = unpack("<" + "I" * self.Proprieties.NodeTableLength, data[nodes_offset : nodes_offset + nodes_lenght])

class XMPR_Proprieties:
    STRUCT = Struct("IIII 32s IHHI")
    def __init__(self, data=None):
        self.Hash_PrimitiveName: Crc32
        self.Hash_MaterialName: Crc32
        self.Hash_Unk: Crc32
        self.Hash_VisibilityNode: Crc32
        self.Unk: bytes | list
        self.DrawPriority = 0
        self.PrimitiveType = 0
        self.PrimitiveUnk = 0
        self.NodeTableLength = 0
        
        if data:
            self.read(data)
    
    def read(self, data):
        hash_primitive_name, hash_material_name, hash_unk, hash_visibility_node, \
        self.Unk, \
        self.DrawPriority, self.PrimitiveType, self.PrimitiveUnk, self.NodeTableLength = \
            unpack_from(XMPR_Proprieties.STRUCT.format, data)
        
        self.Hash_PrimitiveName = Crc32(hash_primitive_name)
        self.Hash_MaterialName = Crc32(hash_material_name)
        self.Hash_Unk = Crc32(hash_unk)
        self.Hash_VisibilityNode = Crc32(hash_visibility_node)

class XPRM:
    MAGIC = b"XPRM"
    STRUCT = Struct("<4s II II")
    def __init__(self, data=None):
        self.XPVB: XPVB
        self.XPVI: XPVI
        
        if data:
            self.read(data)
        
    def read(self, data):
        xprm_magic, \
        xpvb_offset, xpvb_lenght, \
        xpvi_offset, xpvi_lenght = \
            unpack_from(XPRM.STRUCT.format, data)
        
        magic_check(xprm_magic, XPRM.MAGIC)
        
        self.XPVB = XPVB(data[xpvb_offset : xpvb_offset + xpvb_lenght])
        self.XPVI = XPVI(data[xpvi_offset : xpvi_offset + xpvi_lenght])

class XPVB:
    MAGIC = b"XPVB"
    HEADER = Struct("<4s HHH HI")
    def __init__(self, data=None):
        self.VertexCount = 0
        self.Vertices: list[dict] = []
        
        if data:
            self.read(data)
    
    def read(self, data):
        xpvb_magic, \
        att_buffer_offset, \
        unk_offset, \
        vertex_buffer_offset, \
        stride, \
        self.VertexCount = \
            unpack_from(XPVB.HEADER.format, data)
        
        magic_check(xpvb_magic, XPVB.MAGIC)
        
        att_buffer = decompress(data[att_buffer_offset : att_buffer_offset + unk_offset])
        aCount = [int] * 10
        aOffset = [int] * 10
        aSize = [int] * 10
        aType = [int] * 10
        off = 0
        for i in range(10):
            aCount[i]  = unpack("<B", att_buffer[off:off+1])[0]; off += 1
            aOffset[i] = unpack("<B", att_buffer[off:off+1])[0]; off += 1
            aSize[i]   = unpack("<B", att_buffer[off:off+1])[0]; off += 1
            aType[i]   = unpack("<B", att_buffer[off:off+1])[0]; off += 1
        
        vertex_buffer = decompress(data[vertex_buffer_offset : stride * self.VertexCount])
        
        for i in range(self.VertexCount):
            buffer = vertex_buffer[(stride * i) : (stride * i) + stride]
            vertex = {"Position": (), "Normal": (), "Texcoord0": (), "Texcoord1": (), "Weight": (), "Nodes": (), "Color": ()}
            for j in range(10):
                if   j == 0: # position
                    vertex["Position"]  = self.unpack_vertex(buffer, aCount[j], aOffset[j], aSize[j], aType[j])
                elif j == 1: # unk
                    pass
                elif j == 2: # normal
                    vertex["Normal"]    = self.unpack_vertex(buffer, aCount[j], aOffset[j], aSize[j], aType[j])
                elif j == 3: # unk
                    pass
                elif j == 4: # uv0
                    vertex["Texcoord0"] = self.unpack_vertex(buffer, aCount[j], aOffset[j], aSize[j], aType[j])
                elif j == 5: # uv1
                    vertex["Texcoord1"] = self.unpack_vertex(buffer, aCount[j], aOffset[j], aSize[j], aType[j])
                elif j == 6: # unk
                    pass
                elif j == 7: # weight
                    vertex["Weight"]    = self.unpack_vertex(buffer, aCount[j], aOffset[j], aSize[j], aType[j])
                elif j == 8: # nodes
                    nodes               = self.unpack_vertex(buffer, aCount[j], aOffset[j], aSize[j], aType[j])
                    vertex["Nodes"]     = (int(nodes[0]), int(nodes[1]), int(nodes[2]), int(nodes[3])) # convert float to int
                elif j == 9: # color
                    vertex["Color"]     = self.unpack_vertex(buffer, aCount[j], aOffset[j], aSize[j], aType[j])
            self.Vertices.append(vertex)
    
    def unpack_vertex(self, buffer, aCount, aOffset, aSize, aType):
        if aCount != 0:
            if aType == 2:
                return unpack("<" + "f" * aCount, buffer[aOffset : aOffset + aSize])
            else:
                raise ValueError(f"UNKNOWN VERTEX TYPE: {aType}")

class XPVI:
    MAGIC = b"XPVI"
    HEADER = Struct("<4s H H I")
    def __init__(self, data=None):
        self.Indices = []
        self.PrimitiveType = 0
        self.IndexCount = 0
        
        if data:
            self.read(data)
    
    def read(self, data):
        xpvi_magic, \
        self.PrimitiveType, \
        indices_offset, \
        self.IndexCount = \
            unpack_from(XPVI.HEADER.format, data)
        
        magic_check(xpvi_magic, XPVI.MAGIC)
        
        index_buffer = decompress(data[indices_offset : ])
        
        if self.PrimitiveType == 0:
            # Triangle list
            #    0      5
            #   / \    / \
            #  1---2  3---4
            off = 0
            for i in range(self.IndexCount // 3):
                self.Indices.append(unpack("<HHH", index_buffer[off : off + 6])); off += 6
        elif self.PrimitiveType == 2:
            # Triangle strip
            #   0---2---4
            #    \ / \ / \
            #     1---3---5
            self.Indices = unpack_from("<" + "H" * self.IndexCount, index_buffer)
