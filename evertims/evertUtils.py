import bmesh
import mathutils
import math
import gpu
from gpu_extras.batch import batch_for_shader

# ############################################################
# Evertims mesh and transform utilities
# ############################################################


# method from the Print3D add-on: create a bmesh from an object
# (for triangulation, apply modifiers, etc.)
def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):

    assert(obj.type == 'MESH')

    if apply_modifiers and obj.modifiers:
        import bpy
        me = obj.to_mesh(bpy.context.scene, True, 'PREVIEW', calc_tessface=False)
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        del bpy
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm


# given a Blender object, return list of faces vertices and associated materials
def getFacesMatVertList(obj):

    # get bmesh
    bm = bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=True)

    # init locals
    facesMatList = []
    facesVertList = []

    # loop over mesh faces
    for face in bm.faces:

        # get material
        slot = obj.material_slots[face.material_index]
        facesMatList.append(slot.material.name)

        # get face vertices
        vertList = []
        for v in face.verts: # browse through vertice index
            vertList = vertList + list(v.co.to_tuple())
        facesVertList.append(vertList)

    return (facesMatList, facesVertList)


# check if 2 input matrices are different above a certain threshold.
def areDifferent_Mat44(mat1, mat2, thresholdLoc = 1.0, thresholdRot = 1.0):

    # init locals
    areDifferent = False

    # extract matrices translation and rotation components
    t1, t2 = mat1.to_translation(), mat2.to_translation()
    r1, r2 = mat1.to_euler(), mat2.to_euler()

    # loop over components xyz (translation) and ypr (rotation), check for differences above threshold
    for n in range(3):

        # check for diff above threshold: translation
        if( abs(t1[n]-t2[n]) > thresholdLoc ): return True

        # check for diff above threshold: rotation
        if( abs(math.degrees(r1[n]-r2[n])) > thresholdRot ): return True

    # default (no difference)
    return False


# convert blender 4x4 matrix to tuple
def mat4x4ToTuple(mat):

    return ( \
        mat[0][0], mat[0][1], mat[0][2], mat[0][3], \
        mat[1][0], mat[1][1], mat[1][2], mat[1][3], \
        mat[2][0], mat[2][1], mat[2][2], mat[2][3], \
        mat[3][0], mat[3][1], mat[3][2], mat[3][3]  \
        )

def draw_line_3d(color, start, end):
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": [start,end]})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
