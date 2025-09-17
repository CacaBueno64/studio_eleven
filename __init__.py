import bpy
import pip

from .operators import *
from .binary import *

if "operators" in locals():
    importlib.reload(import_archive)
    importlib.reload(import_xmpr)
if "binary" in locals():
    importlib.reload(compression)
    importlib.reload(archive)
    importlib.reload(xmpr)
    importlib.reload(joint)
    importlib.reload(resource)

bl_info = {
    "name": "Studio Eleven",
    "category": "Import-Export",
    "description": "Level5 3d model formats support",
    "author": "Tinifan",
    "version": (2, 0),
    "blender": (2, 80, 2),
    "location": "File > Import-Export > Studio Eleven", 
    "warning": "",
    "doc_url": "",
    "support": 'COMMUNITY',
}

class Level5_Menu_Import(bpy.types.Menu):
    bl_label = "Studio Eleven (.xc/.pck/.prm)"
    bl_idname = "TOPBAR_MT_file_level5_import"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportArchive.bl_idname, text="Archive (.xc/.pck)", icon="MESH_DATA")
        layout.operator(ImportXMPR.bl_idname, text="Mesh (.prm)", icon="MESH_DATA")

def draw_menu_import(self, context):
    self.layout.menu(Level5_Menu_Import.bl_idname)

def register():
    bpy.utils.register_class(ImportArchive)
    bpy.utils.register_class(ImportXMPR)
    bpy.utils.register_class(Level5_Menu_Import)
    bpy.types.TOPBAR_MT_file_import.append(draw_menu_import)

def unregister():
    bpy.utils.unregister_class(ImportArchive)
    bpy.utils.unregister_class(ImportXMPR)
    bpy.utils.unregister_class(Level5_Menu_Import)      
    bpy.types.TOPBAR_MT_file_import.remove(draw_menu_import)

if __name__ == "__main__":
    register()
