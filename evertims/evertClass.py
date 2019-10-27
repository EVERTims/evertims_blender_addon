import bpy
import socket
import bgl
from . import ( evertUtils )
from .evertAbstractClasses import *


class EvertRoom(AbstractObj):

    def __init__(self, kx_obj_list):
        """
        Room constructor.

        :param kx_obj_list: list of Blender Object representing EVERTims room
        :type kx_obj: KX_GameObject
        """

        # parent constructor
        super().__init__()

        self.objList = kx_obj_list
        self.osc['header'] = "room"
        self.id = 1

    def start(self):
        
        # parent method
        super().start()

        # init locals
        self.is_updated = True
        self.oldMaterialCollectionList = []
        for obj in self.objList:
            self.oldMaterialCollectionList.append( obj.data.materials )

        # add callback to stack
        bpy.app.handlers.scene_update_pre.append(self.check_for_updates_callback)        


    def stop(self):
        # parent method
        super().stop()
        # remove callback from stack
        bpy.app.handlers.scene_update_pre.remove(self.check_for_updates_callback)


    def update(self):

        # loop over objects in room
        for iObj in range( len( self.objList )):

            # check for material update (doesn't work if only change material name)
            obj = self.objList[iObj]
            oldMaterialCollection = self.oldMaterialCollectionList[iObj]
            
            # material has been updated 
            if (obj.data is not None) and (oldMaterialCollection != obj.data.materials):

                # update locals
                self.oldMaterialCollectionList[iObj] = self.obj.data.materials

                # flag update required
                self.is_updated = True

            # check for geometry update
            # ... (happening in scene callback were it belongs)
        
        # need update
        if( self.is_updated ):

            # unflag update required
            self.is_updated = False

            # send update
            self.sendRoom()

    def check_for_updates_callback(self, scene):

        # check for mesh update based on blender is_updated internal routine
        self.is_updated = self.is_updated or any( obj.is_updated for obj in self.objList )

    def sendRoom(self):
        
        # warn client that room definition is about to start
        self.send("definestart")

        # init loop 
        faceId = 1

        # loop over room objects
        for obj in self.objList:

            # get list of faces vertices with associated materials
            (facesMatList, facesVertList) = evertUtils.getFacesMatVertList(obj)

            # loop over faces
            for iFace in range( len( facesMatList ) ):

                # send face id
                self.send("face", faceId)

                # send face material
                self.send("face/"+str(faceId)+"/material", facesMatList[iFace])

                # send face triangles
                self.send("face/"+str(faceId)+"/triangles/xyz", facesVertList[iFace])

                # increment face id
                faceId += 1

        # end define
        self.send("defineover")


class EvertSourceListener(AbstractMovable):
    """
    Source / Listener object, bridge between the notions of BGE KX_GameObject and EVERTims Listeners / Sources.
    """

    def __init__(self, kx_obj, typeOfInstance):
        """
        Source / Listener constructor.

        :param kx_obj: Blender Object representing EVERTims listener / source
        :param typeOfInstance: precision on the nature of the created object, either 'source' or 'listener'
        :type kx_obj: KX_GameObject
        :type typeOfInstance: String
        """

        # parent constructor
        super().__init__()

        self.obj = kx_obj
        self.osc['header'] = typeOfInstance
        self.id = 1


class EvertSolution():

    def __init__(self):
        self.roomName = ""
        self.sourceName = ""
        self.listenerName = ""
        self.paths = {}

    def print(self, indent = ""):
        print(indent, "room", self.roomName)
        print(indent, "source", self.sourceName)
        print(indent, "listener", self.listenerName)
        print(indent, "number of paths", len(self.paths))


class EvertPath():

    def __init__(self):
        self.order = -1
        self.length = -1
        self.points = None
        self.reflectance = None

    def print(self, indent = ""):
        print(indent, "order", self.order)
        print(indent, "length", self.length)
        if( self.points ):
            print(indent, "points", self.points)
        if( self.reflectance ):
            print(indent, "reflectance", self.reflectance)


class RayManager():
    """
    Ray manager class: handle Ray objects for raytracing visual feedback.
    """

    def __init__(self, serverAddress):
        """
        Ray manager constructor.

        :param sock: socket with which the ray manager communicates with the EVERTims client.
        :param sock_size: size of packet read every pass (sock.recv(sock_size))
        :param dbg: enable debug (print log in console)
        :type sock: Socket
        :type sock_size: Integer
        :type dbg: Boolean
        """
        # self.sock = sock
        # self.sock_size = sock_size
        
        self.dbg = False
        self.solutions = {}
        self.serverAddress = serverAddress
        self.drawOrderMax = 2

        # self.missedRayCounter = 0

        # define bpy handle
        self.draw_handler_handle = None


    def start(self):
        self.oscServer = OSC.OSCServer(self.serverAddress, max_packet_size=65507) # max packet size matches spat max packet send size
        # self.oscServer = OSC.ThreadingOSCServer(self.serverAddress)
        self.oscServer.addMsgHandler('default', self.oscCallback)
        # self.oscServer.serve_forever()

        # add local pre_draw method to to scene callback
        # (have to do it that way, rays won't be drawn if drawRays called in stadard update method)
        self.draw_handler_handle = bpy.types.SpaceView3D.draw_handler_add(self.drawRays, (None,None), 'WINDOW', 'PRE_VIEW')
        if self.dbg: print('added evertims module raytracing callback to draw_handler')        

    def stop(self):
        self.oscServer.close()

        if self.draw_handler_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler_handle, 'WINDOW')
            self.draw_handler_handle = None
            if self.dbg: print('removed evertims module raytracing callback from draw_handler')

    # WARNING: maybe not the best idea to create instances of solution 
    # and paths dict when processing message
    def oscCallback(self, addr, tags, data, client_address):

        # print('---------------------------------------------------')
        # print('addr ', addr)
        # print('tags ', tags)
        # print('data ', data)
        # print('client address ', client_address)
        # print('---------------------------------------------------')

        if self.dbg:
            print('<- received from', client_address, addr, data)

        # for solutionId, solution in self.solutions.items():
        #     print('solution', solutionId)
        #     solution.print('   ')

        #     # loop over paths
        #     for pathId, path in solution.paths.items():
        #         print('path', pathId)
        #         path.print('      ')

        # unexpected msg
        if( not addr.startswith("/solution") ):
            self.unexpectedMsgAddressWarning(addr)
            return

        # split msg address 
        addrArray = addr.split('/')
        solutionId = addrArray[2]
        arg1 = addrArray[3]
        arg2 = addrArray[4]
        
        # only handling path msg atm
        if( arg1 != 'path'):
            self.unexpectedMsgAddressWarning(addr)
            return

        # discarded flags
        if( arg2 == "created" or arg2 == "number" or arg2 == "updated" ):
            return

        # create solution if need be
        if( not solutionId in self.solutions ):
            self.solutions[solutionId] = EvertSolution()
        solution = self.solutions[solutionId]

        # delete path msg
        if( arg2 == "deleted" ):
            
            pathIds = [pathId for pathId in solution.paths if pathId in data]
            for pathId in pathIds: del solution.paths[pathId]
     
            return 

        # shape data
        pathId = arg2
        pathAttr = addrArray[5]

        # create path if need be
        if( not pathId in solution.paths ):
            solution.paths[pathId] = EvertPath()

        # path length
        if (pathAttr == "length"):
            solution.paths[pathId].length = data[0]


        # path xyz points
        elif (pathAttr == "xyz"):
            
            # sanity check size
            if (len(data) % 3 != 0):
                print ("wrong format of path point coordinates (not a mult. of 3).", len(data), " float received. path update ignored")
                return

            # extract data
            numPoints = int( len(data) / 3 )
            solution.paths[pathId].order = numPoints - 2
            solution.paths[pathId].points = []

            for iPoint in range(numPoints):
                solution.paths[pathId].points.append( ( data[iPoint * 3 + 0], data[iPoint * 3 + 1], data[iPoint * 3 + 2] ) )


        # # path order
        # elif (pathAttr == "order"):
        #     solution.paths[pathId].order = data[0]
        #     print('path order', data)

        # path reflectance
        elif (pathAttr == "reflectance"):
            solution.paths[pathId].reflectance = data

        # known yet non-processed messages
        elif (pathAttr == "image" or pathAttr == "delay"):
            return 
        
        # unexpected message address warning
        else:
            self.unexpectedMsgAddressWarning( addr );


    def drawRays(self, bpy_dummy_self, bpy_dummy_context):
        """
        Invoke draw methods from rays in local dict
        """

        # loop over solutions
        for solutionId, solution in self.solutions.items():

            # loop over paths
            for pathId, path in solution.paths.items():

                if( path.order > self.drawOrderMax ):
                    continue

                # loop over points (segments)
                for iPoint in range(len(path.points)-1):

                    p1 = path.points[iPoint]
                    p2 = path.points[iPoint+1]

                    bgl.glColor4f(0.8,0.8,0.9,0.01)
                    bgl.glLineWidth(0.01)

                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex3f(p1[0],p1[1],p1[2])
                    bgl.glVertex3f(p2[0],p2[1],p2[2])
                    bgl.glEnd()

                    bgl.glNormal3f(0.0,0.0,1.0)
                    bgl.glShadeModel(bgl.GL_SMOOTH);

    def unexpectedMsgAddressWarning(self, addr):
        print("received osc message not handled: " + msg.addr)

    def update(self):
        self.oscServer.handle_request()

    # def crystalizeVisibleRays(self):
    #     """
    #     Convert all existing rays into curves, added to the blender scene, not deleted when the simulation stops
    #     """

    #     # discard if no rays to draw
    #     if( len( self.rayDict ) == 0 ):
    #         return

    #     # create the Curve Datablock
    #     curveData = bpy.data.curves.new('EvertRay', type='CURVE')
    #     curveData.dimensions = '3D'
    #     curveData.resolution_u = 2

    #     # map coords to spline
    #     polyline = curveData.splines.new('POLY')
    #     polyline.points.add( len(self.rayDict)*2 )
    #     count = 0
    #     for rayID, ray in self.rayDict.items():
    #         polyline.points[count].co = (ray.p1[0], ray.p1[1], ray.p1[2], 1)
    #         count += 1
    #         polyline.points[count].co = (ray.p2[0], ray.p2[1], ray.p2[2], 1)
    #         count += 1
    #         print( "{} {} {}".format(ray.p1[0], ray.p1[1], ray.p1[2]))
    #         print( "{} {} {}".format(ray.p2[0], ray.p2[1], ray.p2[2]))


    #     # create Object
    #     curveOB = bpy.data.objects.new('EvertRay', curveData)
    #     curveData.bevel_depth = 0.01

    #     # attach to scene and validate context
    #     scn = bpy.context.scene
    #     scn.objects.link(curveOB)
    #     scn.objects.active = curveOB

