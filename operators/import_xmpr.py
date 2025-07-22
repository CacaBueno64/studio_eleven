import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, EnumProperty

from ..binary import xmpr
from ..utils import *

def make_mesh(xmpr_mesh: xmpr.XMPR, armature=None, bones=None, lib=None, txp=None):
    # create the mesh
    mesh_name = xmpr_mesh.PrimitiveName.decode("shift-jis")
    mesh = bpy.data.meshes.new(name=mesh_name)
    mesh_obj = bpy.data.objects.new(name=mesh_name, object_data=mesh)
    
    bpy.context.collection.objects.link(mesh_obj)
    
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # get vertices
    positions = []; normals = []; texcoord0 = []; texcoord1 = []; colors = []
    for i in range(xmpr_mesh.XPRM.XPVB.VertexCount):
        positions.append(axis_convert(xmpr_mesh.XPRM.XPVB.Vertices[i]["Position"]))
        normals.append(axis_convert(xmpr_mesh.XPRM.XPVB.Vertices[i]["Normal"]))
        texcoord0.append(uv_convert(xmpr_mesh.XPRM.XPVB.Vertices[i]["Texcoord0"]))
        texcoord1.append(uv_convert(xmpr_mesh.XPRM.XPVB.Vertices[i]["Texcoord1"]))
        colors.append(xmpr_mesh.XPRM.XPVB.Vertices[i]["Color"])
    indices   = xmpr_mesh.XPRM.XPVI.Indices
    if xmpr_mesh.XPRM.XPVI.PrimitiveType == 2:
        indices = triangulate([indices])
    
    # draw the vertex positions and faces
    mesh.from_pydata(positions, [], indices)
    # draw the vertex normals
    if normals:
        mesh.normals_split_custom_set_from_vertices(normals)
    # draw the vertex texcoords
    texprojs = ["UVMap0", "UVMap1"]
    # slot 0
    if texcoord0:
        uv_layer0 = mesh.uv_layers.new(name=texprojs[0])
        for loop in mesh.loops:
            vertex_index = loop.vertex_index
            if vertex_index < len(texcoord0):
                uv_layer0.data[loop.index].uv = texcoord0[vertex_index]
        mesh_obj.modifiers.new(name=texprojs[0], type="UV_WARP")
        mesh_obj.modifiers[texprojs[0]].uv_layer = texprojs[0]
    # slot 1
    if texcoord1:
        uv_layer1 = mesh.uv_layers.new(name=texprojs[1])
        for loop in mesh.loops:
            vertex_index = loop.vertex_index
            if vertex_index < len(texcoord1):
                uv_layer1.data[loop.index].uv = texcoord1[vertex_index]
        mesh_obj.modifiers.new(name=texprojs[1], type="UV_WARP")
        mesh_obj.modifiers[texprojs[1]].uv_layer = texprojs[1]
    # draw the vertex colors
    if colors:
        color_layer = mesh.vertex_colors.new(name="Col")
        for loop_idx, color in enumerate(colors):
            color_layer.data[loop_idx].color = color

def fileio_import_xmpr(context, filepath=None, data=None):
    if filepath:
        with open(filepath, "rb") as file:
            data = file.read()
    mesh = xmpr.XMPR(data)
    
    make_mesh(mesh)
    
    return {'FINISHED'}

# REGISTER CLASS
class ImportXMPR(bpy.types.Operator, ImportHelper):
    bl_idname = "import.prm"
    bl_label = "Import a .prm"
    bl_options = {'PRESET', 'UNDO'}
    filename_ext = ".prm"
    filter_glob: StringProperty(default="*.prm", options={'HIDDEN'})
    
    def execute(self, context):
        return fileio_import_xmpr(context, filepath=self.filepath)
