import bpy
import socket
import bgl
from . import ( evertUtils )
from .evertAbstractClasses import *
import time


# ############################################################
# Evertims classes (room, source, etc.)
# ############################################################


class EvertRoom(AbstractObj):

    def __init__(self, objList):

        # parent constructor
        super().__init__()

        # save list of room objects to local
        self.objList = objList

        # init locals
        self.osc['header'] = "room"
        self.id = 1

        # throttle (time) udpate mechanism
        self.udpateInterval = 1 # in sec
        self.nextUpdateTime = 0 # in sec
        self.is_udpated_tmp = False


    # called upon auralization start
    def start(self):

        # parent method
        super().start()

        # init locals
        self.is_updated = True

        # add callback to stack
        bpy.app.handlers.depsgraph_update_post.append(self.check_for_updates_callback)


    # called upon auralization stop
    def stop(self):

        # parent method
        super().stop()

        # remove callback from stack
        bpy.app.handlers.depsgraph_update_post.remove(self.check_for_updates_callback)


    # running callback
    def update(self):

        # discard if no update required
        if not self.is_updated:
            return

        # check if time to update (local throttle on room update)
        currentTime = time.time()
        if( currentTime < self.nextUpdateTime ):
            return

        # update running timer
        self.nextUpdateTime = currentTime + self.udpateInterval

        # send update
        self.sendRoom()

        # unflag update required
        self.is_updated = False

        # debug
        print('+++ update room')

    # local callback called from depsgraph_update_post stack to get immediate access to room objects
    # is_updated attribute (could switch False-True-False between two calls of self.update()
    # method otherwise)
    def check_for_updates_callback(self, scene, depsgraph):

        # no need for further check if update already planned (material changed)
        if( self.is_updated ):
            return

        # @todo: optimize
        for update in depsgraph.updates:
            for obj in self.objList:
                # if update.id.original == active_obj and update.is_updated_geometry or update.is_updated_transform:
                if update.id.original == obj:
                    self.is_updated = True


    # send room geometry to client
    def sendRoom(self):

        # warn client that room definition is about to start
        self.send("definestart")

        # init loop
        faceId = 1

        # loop over room objects
        for obj in self.objList:

            # discard if object not a mesh
            if obj.type != 'MESH':
                continue

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

    def __init__(self, obj, typeOfInstance):

        # parent constructor
        super().__init__()

        # init locals
        self.obj = obj
        self.osc['header'] = typeOfInstance
        self.id = 1


# used by ray manager. solutions are sent by Evertims client to ray drawer. a unique solution
# is created for each combination of source/listener/room in the scene
class EvertSolution():

    def __init__(self):

        # init locals
        self.roomName = ""
        self.sourceName = ""
        self.listenerName = ""
        self.paths = {}

    # print solution to console
    def print(self, indent = ""):
        print(indent, "room", self.roomName)
        print(indent, "source", self.sourceName)
        print(indent, "listener", self.listenerName)
        print(indent, "number of paths", len(self.paths))

# used by ray manager, a path is a collection of points that represent an acoustic path
class EvertPath():

    def __init__(self):

        # init locals
        self.order = -1
        self.length = -1
        self.points = None
        self.reflectance = None

    # print path to console
    def print(self, indent = ""):
        print(indent, "order", self.order)
        print(indent, "length", self.length)
        if( self.points ): print(indent, "points", self.points)
        if( self.reflectance ): print(indent, "reflectance", self.reflectance)


# receive messages from Evertims client, shape them into rays, drawn in 3D scene for debug
class RayManager():

    def __init__(self, serverAddress):

        # serverAddress is a tuple (ip, port), used to connect read socket
        self.serverAddress = serverAddress

        # max packet size matches spat max packet send size
        self.maxPacketSize = 65507

        # init locals
        self.dbg = False
        self.solutions = {}
        self.drawOrderMax = 2

        # define bpy handle
        self.draw_handler_handle = None


    # called upon auralization start
    def start(self):

        # init osc server (receive messages, feed them to oscCallback)
        self.oscServer = OSC.OSCServer(self.serverAddress, max_packet_size=self.maxPacketSize)
        # self.oscServer = OSC.ThreadingOSCServer(self.serverAddress)

        # define osc server default callback
        self.oscServer.addMsgHandler('default', self.oscCallback)

        # add local pre_draw method to to scene callback
        # (have to do it that way, rays won't be drawn if drawRays called in stadard update method)
        self.draw_handler_handle = bpy.types.SpaceView3D.draw_handler_add(self.drawRays, (None,None), 'WINDOW', 'POST_VIEW')
        if self.dbg: print(self.__class__.__name__, 'added evertims module raytracing callback to draw_handler')


    # called upon auralization stop
    def stop(self):

        # close listening server
        self.oscServer.close()

        # remove draw callback from blender stack if need be
        if self.draw_handler_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler_handle, 'WINDOW')
            self.draw_handler_handle = None
            if self.dbg: print(self.__class__.__name__, 'removed evertims module raytracing callback from draw_handler')


    # callback invoked by osc server upon message received
    def oscCallback(self, addr, tags, data, client_address):

        # print('---------------------------------------------------')
        # print('addr ', addr)
        # print('tags ', tags)
        # print('data ', data)
        # print('client address ', client_address)
        # print('---------------------------------------------------')

        # for solutionId, solution in self.solutions.items():
        #     print('solution', solutionId)
        #     solution.print('   ')
        #     for pathId, path in solution.paths.items():
        #         print('path', pathId)
        #         path.print('      ')

        # debug
        if self.dbg: print(self.__class__.__name__, '<- received from', client_address, addr, data)

        # discard unexpected msg
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

        # msg: discarded messages
        if( arg2 == "created" or arg2 == "number" or arg2 == "updated" ):
            return

        # create solution if need be
        if( not solutionId in self.solutions ):
            self.solutions[solutionId] = EvertSolution()
        solution = self.solutions[solutionId]

        # msg: delete path
        if( arg2 == "deleted" ):

            # get list of pathId to delete from solution.paths dict
            pathIds = [pathId for pathId in solution.paths if pathId in data]
            for pathId in pathIds: del solution.paths[pathId]

            return

        # shape data
        pathId = arg2
        pathAttr = addrArray[5]

        # create path if need be
        if( not pathId in solution.paths ):
            solution.paths[pathId] = EvertPath()

        # msg: path length
        if( pathAttr == "length" ):
            solution.paths[pathId].length = data[0]


        # msg: path xyz points
        elif( pathAttr == "xyz" ):

            # sanity check size
            if( len(data) % 3 != 0 ):
                print ("wrong format of path point coordinates (not a mult. of 3).", len(data), " float received. path update ignored")
                return

            # extract data
            numPoints = int( len(data) / 3 )
            solution.paths[pathId].order = numPoints - 2
            solution.paths[pathId].points = []

            # create solution path points
            for iPoint in range(numPoints):
                solution.paths[pathId].points.append( ( data[iPoint * 3 + 0], data[iPoint * 3 + 1], data[iPoint * 3 + 2] ) )

        # # path order
        # elif (pathAttr == "order"):
        #     solution.paths[pathId].order = data[0]
        #     print('path order', data)

        # msg: path reflectance
        elif( pathAttr == "reflectance" ):
            solution.paths[pathId].reflectance = data

        # msg: known yet non-processed
        elif( pathAttr == "image" or pathAttr == "delay" ): return

        # unexpected message address warning
        else: self.unexpectedMsgAddressWarning( addr );


    # draw rays callback, added to Bender stack of draw methods
    def drawRays(self, operator, context):

        # init bgl
        bgl.glLineWidth(10)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

        # loop over solutions
        for solutionId, solution in self.solutions.items():

            # loop over paths
            for pathId, path in solution.paths.items():

                # discard draw if path order above limit
                if( path.order > self.drawOrderMax ):
                    continue

                # loop over points (segments)
                for iPoint in range(len(path.points)-1):

                    p1 = path.points[iPoint]
                    p2 = path.points[iPoint+1]

                    evertUtils.draw_line_3d((0.8, 0.8, 0.9, 0.7), p1, p2)

                    # bgl.glColor4f(0.8,0.8,0.9,0.01)
                    # bgl.glLineWidth(0.01)

                    # bgl.glBegin(bgl.GL_LINES)
                    # bgl.glVertex3f(p1[0],p1[1],p1[2])
                    # bgl.glVertex3f(p2[0],p2[1],p2[2])
                    # bgl.glEnd()

                    # bgl.glNormal3f(0.0,0.0,1.0)
                    # bgl.glShadeModel(bgl.GL_SMOOTH);

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

    # debug: print unexpected osc msg to console
    def unexpectedMsgAddressWarning(self, addr):
        print("received osc message not handled: " + msg.addr)


    # running callback
    def update(self):
        self.oscServer.handle_request()


    # Convert existing rays into curves that will remain in the blender scene after auralization stops
    def crystalizeVisibleRays(self):

        # get segment count
        pathsPoints = self.getListOfVisibleSegments()

        # discard if empty
        if( len(pathsPoints) == 0 ): return

        # create the Curve Datablock
        curveData = bpy.data.curves.new('EvertRay', type='CURVE')
        curveData.dimensions = '3D'
        curveData.fill_mode = 'FULL'
        curveData.resolution_u = 1

        # loop over paths
        for pathPoints in pathsPoints:

            # create new spline
            polyline = curveData.splines.new('POLY')

            # create points (spline already has one)
            polyline.points.add( len(pathPoints) - 1 )

            # loop over path points
            for iPoint in range( len(pathPoints) ):

                # set polyline points start / end positions
                p = pathPoints[iPoint]
                polyline.points[iPoint].co = (p[0], p[1], p[2], 1)

        # create Object
        curveOB = bpy.data.objects.new('EvertRay', curveData)
        curveData.bevel_depth = 0.01

        # link object to current collection
        bpy.context.collection.objects.link(curveOB)


    # count total number of segment if current solutions
    def getListOfVisibleSegments(self):

        # init locals
        pathsPoints = []

        # loop over solutions
        for solutionId, solution in self.solutions.items():

            # loop over paths
            for pathId, path in solution.paths.items():

                # discard draw if path order above draw limit
                if( path.order > self.drawOrderMax ): continue

                # init list of points
                pathPoints = []

                # loop over points in path
                for p in path.points:

                    # extract segment points coordinates
                    pathPoints.append( [round(p[0],2),round(p[1],2),round(p[2],2)] )

                # save segments back to local
                pathsPoints.append(pathPoints)

        return pathsPoints
