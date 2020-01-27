import json
import bpy

def dict2str(d):
    return json.dumps(d)

def str2dict(s):
    return json.loads(s) 

def loadMaterialFile(filePath):

    fileObj  = open(filePath, 'r')
    matDict = dict()

    # loop over lines (one per material)
    lines = fileObj.readlines()
    for line in lines:
        if( line.startswith('/material/name') ):
            l = line.lstrip().split(' ')
            name = l[1].rstrip()
            # seemingly stupid, will later be used to store e.g. absorption values
            matDict[name] = ''

    # return mat list
    return matDict

def loadMaterials(context, evertims, forceUpdate = False):

    # sanity check: room materials are acoustic materials
    if forceUpdate or not evertims.materials:

        # get material file path
        addon_prefs = context.user_preferences.addons[__package__].preferences

        # load material file if path defined
        if addon_prefs.material_file_path:
            filePath = bpy.path.abspath(addon_prefs.material_file_path)
            matDict = loadMaterialFile(filePath)
            evertims.materials = dict2str(matDict)
                
        # return error otherwise
        else:
            return ({'ERROR'}, 'undefined material file path')

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
        return({'ERROR'}, 'room group is empty')

    # sanity check: all objects in room group have acoustic materials
    for obj in roomObjects:

        # get object materials
        materialSlots = obj.material_slots

        # abort if no material defined
        if( len( materialSlots ) == 0 ):
            return({'ERROR'}, 'room object ' + obj.name +' has no material')

        # get list of acoustic materials
        matDict = str2dict(evertims.materials)

        # loop over materials in object, check if member of acoustic materials 
        for mat in materialSlots:
            if not mat.name in matDict:
                return({'ERROR'}, 'room object ' + obj.name +' material ' + mat.name + ': not an acoustic material')

    # notify success
    return ({'PASS'}, '')
