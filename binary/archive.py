from ..utils import *
from .compression import *

from struct import pack, unpack, unpack_from, Struct
import zlib

class Archive:
    HEADER_V2 = Struct("<BB HHHHHI")
    FILE_ENTRY_V2 = Struct("<IHHHBB")
    MAGIC_V1 = b"XFSP"
    MAGIC_V2 = b"XPCK"
    def __init__(self, data=None):
        self.Files: dict[str, bytes] = {}
        
        if data:
            self.read(data)
    
    def read(self, data):
        magic = data[ : 4]
        
        if magic == b"XFSP":
            files = {}
            file_count = unpack("<H", data[4:6])[0] & 0xFFF
            file_info_offset = unpack("<H", data[6:8])[0] * 4
            file_table_offset = unpack("<H", data[8:10])[0] * 4
            data_offset = unpack("<H", data[10:12])[0] * 4
            filename_table_size = unpack("<H", data[14:16])[0] * 4
            
            name_table = data[file_table_offset : file_table_offset + filename_table_size]
            name_table = decompress(name_table)
            
            for i in range(file_count):
                unk = unpack("<H", data[file_info_offset + i * 10 + 0 : file_info_offset + i * 10 + 2])[0]
                name_offset = unpack("<H", data[file_info_offset + i * 10 + 2: file_info_offset + i * 10 + 4])[0]
                offset = unpack("<H", data[file_info_offset + i * 10 + 4 : file_info_offset + i * 10 + 6])[0]
                size = unpack("<H", data[file_info_offset + i * 10 + 6 : file_info_offset + i * 10 + 8])[0]
                offset_ext = unpack("<B", data[file_info_offset + i * 10 + 8 : file_info_offset + i * 10 + 9])[0]
                size_ext =  unpack("<B", data[file_info_offset + i * 10 + 9 : file_info_offset + i * 10 + 10])[0]
                
                offset |= offset_ext << 16
                size |= size_ext << 16
                offset = offset * 4 + data_offset
                
                file_data = data[offset : offset + size]
                
                # Get name
                name_length = name_table.find(b'\x00', name_offset)
                name = name_table[name_offset:name_length].decode("utf-8")
                
                files[name] = file_data
                
            file_names = list(files.keys())
            file_names.sort()
            sorted_files = {i: files[i] for i in file_names}
            
            self.Files = sorted_files
        elif magic == b"XPCK":
            file_count = unpack("<H", data[4:6])[0] & 0xFFF
            file_info_offset = unpack("<H", data[6:8])[0] * 4
            file_table_offset = unpack("<H", data[8:10])[0] * 4
            data_offset = unpack("<H", data[10:12])[0] * 4
            filename_table_size = unpack("<H", data[14:16])[0] * 4
            
            hash_to_data = {}
            for i in range(file_count):
                name_crc = unpack("<I", data[file_info_offset + i * 12 : file_info_offset + i * 12 + 4])[0]
                offset = unpack("<H", data[file_info_offset + i * 12 + 6 : file_info_offset + i * 12 + 8])[0]
                size = unpack("<H", data[file_info_offset + i * 12 + 8 : file_info_offset + i * 12 + 10])[0]
                offset_ext = unpack("<B", data[file_info_offset + i * 12 + 10 : file_info_offset + i * 12 + 11])[0]
                size_ext = unpack("<B", data[file_info_offset + i * 12 + 11 : file_info_offset + i * 12 + 12])[0]
                
                offset |= offset_ext << 16
                size |= size_ext << 16
                offset = offset * 4 + data_offset
                
                file_data = data[offset : offset + size]
                
                hash_to_data[name_crc] = file_data
            
            name_table = data[file_table_offset : file_table_offset + filename_table_size]
            name_table = decompress(name_table)
            
            pos = 0
            for i in range(file_count):
                name_length = name_table.find(b'\x00', pos)
                name = name_table[pos:name_length].decode("utf-8")
                pos = name_length + 1
                
                crc = zlib.crc32(name.encode("utf-8"))
                if crc in hash_to_data:
                    self.Files[name] = hash_to_data[crc]
                else:
                    print("Couldn't find", name, hex(crc))
        else:
            raise ValueError(f"File magic not recognized.\nGot: {magic}\nExpected: {b'XFSP'} or {b'XPCK'}")
