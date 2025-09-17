import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, EnumProperty

from .import_xmpr import *
from ..binary import archive, xmpr, joint, resource
from ..utils import *

from mathutils import Vector, Matrix

def fileio_import_archive(context, data):
    arc = archive.Archive(data)
    
    xmpr_data: list[xmpr.XMPR] = []
    mbn_data: list[joint.MBN] = []
    res_data: resource.CHRC = None
    
    for filename in arc.Files:
        if filename.endswith(".xc"):
            fileio_import_archive(arc.Files[filename])
        elif filename == "RES.bin":
            res_data = resource.Resource(arc.Files[filename])
        elif filename.endswith(".prm"):
            xmpr_data.append(xmpr.XMPR(arc.Files[filename]))
        elif filename.endswith(".mbn"):
            mbn_data.append(joint.MBN(arc.Files[filename]))
    
    

# REGISTER CLASS
class ImportArchive(bpy.types.Operator, ImportHelper):
    bl_idname = "import.xpck"
    bl_label = "Import a .xc/.pck"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".xc/.pck"
    filter_glob: StringProperty(default="*.xc", options={'HIDDEN'})
    
    def execute(self, context):
        with open(self.filepath, "rb") as file:
            data = file.read()
        fileio_import_archive(context, data)
        
        return {'FINISHED'}
