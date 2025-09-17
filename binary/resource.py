from ..utils import *
from .compression import decompress

from struct import pack, unpack, unpack_from, Struct
from zlib import crc32

class Resource:
    MAGIC_V1 = b"XRES"
    MAGIC_V2 = b"CHRC00"
    HEADER = Struct("<6s 2x H H HH HH")
    def __init__(self, data=None):
        self.StringTable = {}
        self.Items = {}
        
        if data:
            self.read(data)
    
    def read(self, data):
        data = decompress(data)
        
        if data[ : 6] == Resource.MAGIC_V2:
            self.read_chrc00(data)
        
    def read_chrc00(self, data):
        magic, \
        strTableOffset, unk, \
        matTableOffset, matTableCount, \
        nodeTableOffset, nodeTableCount = \
            unpack_from(Resource.HEADER.format, data)
        
        strTableOffset <<= 2
        matTableOffset <<= 2
        nodeTableOffset <<= 2
        
        self.read_string_table(data[strTableOffset : ])
        
        
        
    def read_string_table(self, data):
        strings = data.split(b"\x00")
        for str in strings:
            self.StringTable[crc32(str)] = str.decode("shift-jis", errors="replace")
            splits = str.split(b".") + str.split(b"_")
            for split in splits:
                self.StringTable[crc32(split)] = split.decode("shift-jis", errors="replace")
