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
