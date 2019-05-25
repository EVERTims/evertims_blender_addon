
import bpy

def isInt(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

# r is round factor
def mat4x4ToString(m, r=3):
    return '{} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} '.format( \
    round(m[0][0], r), round(m[1][0], r), round(m[2][0], r), round(m[3][0], r), \
    round(m[0][1], r), round(m[1][1], r), round(m[2][1], r), round(m[3][1], r), \
    round(m[0][2], r), round(m[1][2], r), round(m[2][2], r), round(m[3][2], r), \
    round(m[0][3], r), round(m[1][3], r), round(m[2][3], r), round(m[3][3], r) )
    
    # this line below works, but spanning the matrix the other way around (row then columns or something)
    # return ' '.join(' '.join('%0.3f' %x for x in y) for y in mat)+'\n'

def write(filepath, lines=[]):
    f = open(filepath, 'w', encoding='utf-8')
    for line in lines:
        f.write("%s\n" % line)
    f.close()

def getVertFaces(ob, use_mesh_modifiers=False):
    """ get vertices and faces from object ob """

    # get the editmode data
    ob.update_from_editmode()

    # get the modifiers
    try:
        mesh = ob.to_mesh(bpy.context.scene, use_mesh_modifiers, "PREVIEW")
    except RuntimeError:
        raise StopIteration

    vertices = mesh.vertices
    faces = mesh.tessfaces

    return (vertices, faces)
