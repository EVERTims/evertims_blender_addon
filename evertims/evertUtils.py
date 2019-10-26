import bmesh
import mathutils
import math

# method from the Print3D add-on
def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
    """
    Returns a transformed, triangulated copy of the mesh
    """

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

    # TODO. remove all customdata layers.
    # would save ram

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm

def getFacesMatVertList(obj):
    
    # get bmesh
    bm = bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=True)
    
    facesMatList = []
    facesVertList = []
    
    # loop over faces
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

def areDifferent_Mat44(mat1, mat2, thresholdLoc = 1.0, thresholdRot = 1.0):
    """
    Check if 2 input matrices are different above a certain threshold.

    :param mat1: input Matrix
    :param mat2: input Matrix
    :param thresholdLoc: threshold above which delta translation between the 2 matrix has to be for them to be qualified as different
    :param thresholdRot: threshold above which delta rotation between the 2 matrix has to be for them to be qualified as different
    :type mat1: mathutils.Matrix
    :type mat2: mathutils.Matrix
    :type thresholdLoc: Float
    :type thresholdRot: Float
    :return: a boolean stating wheter the two matrices are different
    :rtype: Boolean
    """
    areDifferent = False
    jnd_vect = mathutils.Vector((thresholdLoc,thresholdLoc,thresholdRot))
    t1, t2 = mat1.to_translation(), mat2.to_translation()
    r1, r2 = mat1.to_euler(), mat2.to_euler()
    for n in range(3):
        if (abs(t1[n]-t2[n]) > thresholdLoc) or (abs(math.degrees(r1[n]-r2[n])) > thresholdRot): areDifferent = True
    return areDifferent

def mat4x4ToTuple(mat):
    
    return ( \
        mat[0][0], mat[1][0], mat[2][0], mat[3][0], \
        mat[0][1], mat[1][1], mat[2][1], mat[3][1], \
        mat[0][2], mat[1][2], mat[2][2], mat[3][2], \
        mat[0][3], mat[1][3], mat[2][3], mat[3][3]  \
        )    