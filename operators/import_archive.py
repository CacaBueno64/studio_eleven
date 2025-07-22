import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, EnumProperty

from .import_xmpr import *
from ..binary import *
from ..utils import *

def fileio_import_archive(context, data):
    arc = archive.Archive(data)
    
    xmpr_data: list[xmpr.XMPR] = []
    
    for filename in arc.Files:
        if filename.endswith((".xc", ".xv")):
            fileio_import_archive(arc.Files[filename])
        elif filename.endswith(".prm"):
            xmpr_data.append(xmpr.XMPR(arc.Files[filename]))
    
    #if xmpr_data:
    #    for mesh_data in xmpr_data:
    #        make_mesh(mesh_data)

# REGISTER CLASS
class ImportArchive(bpy.types.Operator, ImportHelper):
    bl_idname = "import.xpck"
    bl_label = "Import a .xc/.pck"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".xc/.pck"
    filter_glob: StringProperty(default="*.xc, *.pck", options={'HIDDEN'})
    
    def execute(self, context):
        with open(self.filepath, "rb") as file:
            data = file.read()
        fileio_import_archive(context, data)
        
        return {'FINISHED'}
