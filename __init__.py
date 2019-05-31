
bl_info = {
    "name": "Evertims export",
    "author": "David Poirier-Quinot",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "File > Import-Export > Evertims",
    "description": "Export Evertims files",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export",
}

"""
Export Evertims files (ascii)

- Export doesn't support non triangle faces

"""

if "bpy" in locals():
    import importlib

    if "utils" in locals():
        importlib.reload(utils)
    else:
        from . import utils

import os
import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy.types import Operator


class ExportEvertims(Operator):

    """Save triangle mesh data from the rooms in the scene, along with transform matrices of sources and listeners"""

    bl_idname = "export_mesh.evertims"
    bl_label = "Export Evertims"

    filename_ext = ".txt"
    filter_glob = StringProperty(default="*.txt", options={'HIDDEN'})

    use_selection = BoolProperty(
            name="Selection Only",
            description="Export selected objects only",
            default=False,
            )

    use_mesh_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply the modifiers before saving",
            default=True,
            )

    filepath = StringProperty(
            name="File Path",
            description="Filepath used for exporting the file",
            maxlen=1024,
            subtype='FILE_PATH',
            )

    def invoke(self, context, event):
        wm = context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        from . import utils

        scene = context.scene

        # use either only selected objects or browse all scene
        if self.use_selection:
            objects = context.selected_objects
        else:
            objects = scene.objects

        # get rooms, sources, listeners from objects set
        radicalRoom = "Room"
        radicalSource = "Source"
        radicalListener = "Listener"
        keysRoom = [key for key, value in objects.items() if value.name.startswith(radicalRoom)]
        keysSource = [key for key, value in objects.items() if value.name.startswith(radicalSource)]
        keysListener = [key for key, value in objects.items() if value.name.startswith(radicalListener)]

        # sanity check init
        passCheck = True
        error = "undefined error"

        # sanity check: at least one room, one source, one listener
        if( len(keysRoom) == 0 ):
            error = "define at least one object which name starts with {}".format(radicalRoom)
            passCheck = False
        elif( len(keysSource) == 0 ):
            error = "define at least one object which name starts with {}".format(radicalSource)
            passCheck = False            
        elif( len(keysListener) == 0 ):
            error = "define at least one object which name starts with {}".format(radicalListener)
            passCheck = False

        # sanity check: naming convention respected
        if( passCheck ):
            for key in keysRoom + keysSource + keysListener:
                splitName = objects[key].name.split("_")
                if( len(splitName) != 2 or not utils.isInt(splitName[1]) ):
                    passCheck = False
                    error = "name convention Object_Integer not respected for object: {}".format(objects[key].name)
                    break

        # sanity check: room has at least one material
        if( passCheck ):
            for key in keysRoom:
                if( len(objects[key].data.materials) == 0 ):
                    passCheck = False
                    error = "room {} has no materials assigned".format(objects[key].name)

        # sanity check: report error
        if( not passCheck ):
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        # get export content: init
        lines = []
        
        # get export content: room
        for key in keysRoom:

            id = objects[key].name.split("_")[1]
            obj = objects[key]

            # start room definition
            header = "/room/" + id + "/"
            lines.append(header + "spawn")
            lines.append(header + "definestart")

            # loop over faces
            (vertices, faces) = utils.getVertFaces(obj)
            faceCount = 0
            for faceId, face in enumerate(faces):
                
                # sanity check on num vertice in face
                if len(face.vertices) not in [3, 4]:
                    self.report({'ERROR'}, 'only support triangle faces (object: {})'.format(obj.name))
                    return {'CANCELLED'}
                
                # get face id
                id = str(faceCount)
                
                # announce face msg
                lines.append(header + 'face ' + id)
                
                # export face material 
                mat = obj.data.materials[face.material_index]
                lines.append(header + 'face/' + id + '/material ' + mat.name)

                r = 2 # round factor

                # face is triangle
                if len(face.vertices) == 3:
                    
                    # loop over vertices: init
                    faceCoord = ''
                    
                    # loop over vertices 
                    for vertId in face.vertices:
                        faceCoord += '{} {} {} '.format( round(vertices[vertId].co[0],r),  round(vertices[vertId].co[1]),  round(vertices[vertId].co[2]) )
                    lines.append( header + 'face/' + id + '/triangles/xyz ' + faceCoord)
                    
                elif len(face.vertices) == 4:

                    # loop over vertices: init
                    faceCoord = ''   

                    # loop over vertices
                    for vertIdTmp in [0, 1, 2]:
                        vertId = face.vertices[vertIdTmp]
                        faceCoord += '{} {} {} '.format( round(vertices[vertId].co[0],r),  round(vertices[vertId].co[1]),  round(vertices[vertId].co[2]) )
                    lines.append( header + 'face/' + id + '/triangles/xyz ' + faceCoord)

                    # incr. face count
                    faceCount += 1
                    id = str(faceCount)

                    # announce face msg (to factorize)
                    lines.append(header + 'face ' + id)
                    
                    # export face material 
                    lines.append(header + 'face/' + id + '/material ' + mat.name)

                    faceCoord = ''
                    for vertIdTmp in [2, 3, 0]:
                        vertId = face.vertices[vertIdTmp]
                        faceCoord += '{} {} {} '.format( round(vertices[vertId].co[0],r),  round(vertices[vertId].co[1]),  round(vertices[vertId].co[2]) )
                    lines.append( header + 'face/' + id + '/triangles/xyz ' + faceCoord)

                # incr. face count
                faceCount += 1
            
            # end room definition
            lines.append(header + "defineover")        
        
        # get export content: listener
        for key in keysListener:
            id = objects[key].name.split("_")[1]
            header = "/listener/" + id + "/"
            lines.append(header + "spawn")
            lines.append(header + "transform/matrix " + utils.mat4x4ToString(objects[key].matrix_world))
        
        # get export content: listener
        for key in keysSource:
            id = objects[key].name.split("_")[1]
            header = "/source/" + id + "/"
            lines.append(header + "spawn")
            lines.append(header + "transform/matrix " + utils.mat4x4ToString(objects[key].matrix_world))

        # write to disk
        utils.write(self.filepath, lines)

        return {'FINISHED'}


def menu_export(self, context):
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".txt"
    self.layout.operator(ExportEvertims.bl_idname, text="Evertims (.txt)")


def register():
    bpy.utils.register_module(__name__)

    # bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    # bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
