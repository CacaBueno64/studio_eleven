from ..utils import *

from struct import pack, unpack, unpack_from, Struct

class MBN:
    HEADER = Struct("<III")
    def __init__(self, data=None):
        self.Name = ""
        self.ParentName = ""
        self.Hash_Name = 0
        self.Hash_ParentName = 0
        
        self.Type = 0
        
        self.Translation     = [0.0, 0.0, 0.0]
        
        self.Rotation       = [[1.0, 0.0, 0.0],
                               [0.0, 1.0, 0.0],
                               [0.0, 0.0, 1.0]]
        
        self.Scale           = [1.0, 1.0, 1.0]
        
        self.LocalRotation  = [[1.0, 0.0, 0.0],
                               [0.0, 1.0, 0.0],
                               [0.0, 0.0, 1.0]]
        
        self.HeadTranslation = [0.0, 0.0, 0.0]
        
        self.HeadRotation   = [[1.0, 0.0, 0.0],
                               [0.0, 1.0, 0.0],
                               [0.0, 0.0, 1.0]]
        
        self.HeadScale       = [0.0, 0.0, 0.0]
        
        if data:
            self.read(data)
    
    def read(self, data):
        self.Hash_Name, self.Hash_ParentName, \
        self.Type = \
            unpack_from(MBN.HEADER.format, data)
        
        data = data[12:]
        self.Translation     = unpack_vector(data, 3)
        data = data[12:]
        self.Rotation        = unpack_matrix(data, 3, 3)
        data = data[36:]
        self.Scale           = unpack_vector(data, 3)
        data = data[12:]
        self.LocalRotation   = unpack_matrix(data, 3, 3)
        data = data[36:]
        self.HeadTranslation = unpack_vector(data, 3)
        data = data[12:]
        self.HeadRotation    = unpack_matrix(data, 3, 3)
        data = data[36:]
        self.HeadScale       = unpack_vector(data, 3)
