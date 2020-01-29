import json
import bpy
from .evertims import ( EvertMaterial )

def dict2str(d):
    return json.dumps(d)

def str2dict(s):
    return json.loads(s) 

# convert dict of mat to dict of arrays, json dumpable
def matDict2str(matDict):

    d = dict()
    for m in matDict: 
        d[m] = [matDict[m].frequencies, matDict[m].absorptions, matDict[m].diffusions]

    return dict2str(d)

# convert back
def str2matDict(s):

    d = json.loads(s)
    matDict = dict()

    for m in d: 
        matDict[m] = EvertMaterial(m)
        matDict[m].frequencies = d[m][0]
        matDict[m].absorptions = d[m][1]
        matDict[m].diffusions = d[m][2]
        
    return matDict

# check if a file can be created at filePath
def isValidExportPath(filePath):

    if( not filePath.lower().endswith('.txt') ):
        return({'ERROR'}, 'Export file should be a .txt')

    try:
        open(filePath,'w')
        return({'PASS'}, '')
    except IOError:
        return({'ERROR'}, 'Invalid export file path')


def loadMaterialFile(filePath):

    fileObj  = open(filePath, 'r')
    matDict = dict()

    # loop over lines 
    lines = fileObj.readlines()
    for line in lines:

        # shape data 
        l = line.lstrip().split(' ')
        header = l[0]

        # detect new material addition
        if( header.startswith('/material/name') ):

            # shape data
            name = l[1].rstrip()
            
            # save to locals
            matDict[name] = EvertMaterial(name)
        
        else:

            # shape data
            values = [float(x) for x in l[1::]]

            # detect frequencies definition
            if( header.endswith('/frequencies') ):
                matDict[name].frequencies = values

            # detect frequencies definition
            elif( header.endswith('/absorption') ):
                matDict[name].absorptions = values

    # return mat list
    return matDict


def checkMaterialsIntegrity(matDict):

    # loop over materials
    for k in matDict:

        m = matDict[k]

        # check that at least one frequency is defined
        if( len(m.frequencies) == 0 ):
            return({'ERROR'}, 'Material ' + m.name + ' missing frequencies definition')

        # check that material has same number of absorption and frequencies
        if( len(m.frequencies) != len(m.absorptions) ):
            return({'ERROR'}, 'Material ' + m.name + ' number of absorption coefs does not match number of frequencies defined')

    # all passed
    return({'PASS'}, '')


def loadMaterials(context, evertims, forceUpdate = False):

    # sanity check: room materials are acoustic materials
    if forceUpdate or not evertims.materials:

        # get material file path
        addon_prefs = context.user_preferences.addons[__package__].preferences

        # load material file if path defined
        if addon_prefs.material_file_path:
            filePath = bpy.path.abspath(addon_prefs.material_file_path)
            matDict = loadMaterialFile(filePath)

            # check material integrity
            (status, msg) = checkMaterialsIntegrity(matDict)
            if status != {'PASS'}:
                return (status, msg)

            # shape output
            evertims.materials = matDict2str(matDict)
                
        # return error otherwise
        else:
            return ({'ERROR'}, 'Undefined material file path')

    else: print('evertims.material already defined, skipping init')

    # notify success
    return ({'PASS'}, '')

def checkSceneIntegrity(context, evertims):

    # sanity check: room defined
    if not evertims.room_group:
        return({'ERROR'}, 'No room defined')

    # sanity check: source defined
    if not evertims.source_object:
        return({'ERROR'}, 'No source defined')

    # sanity check: listener defined
    if not evertims.listener_object:
        return({'ERROR'}, 'No listener defined')

    # load materials if need be
    (status, msg) = loadMaterials(context, evertims)
    if status != {'PASS'}:
        return (status, msg)

    # sanity check: room group contains at least one object
    roomObjects = bpy.data.groups[evertims.room_group].objects
    if( len(roomObjects) == 0 ):
        return({'ERROR'}, 'Room group is empty')

    # sanity check: all objects in room group have acoustic materials
    for obj in roomObjects:

        # get object materials
        materialSlots = obj.material_slots

        # abort if no material defined
        if( len( materialSlots ) == 0 ):
            return({'ERROR'}, 'Room object ' + obj.name +' has no material')

        # get list of acoustic materials
        matDict = str2dict(evertims.materials)

        # loop over materials in object, check if member of acoustic materials 
        for mat in materialSlots:
            if not mat.name in matDict:
                return({'ERROR'}, 'Room object ' + obj.name +' material ' + mat.name + ': not an acoustic material')

    # notify success
    return ({'PASS'}, '')
