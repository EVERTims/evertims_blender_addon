import bpy
from .evertClass import *
from . import OSC

class Evertims(AbstractOscSender):
    """
    Main EVERTims python module. Send scene information
    (room geometry, materials, listener and source position, etc.)
    to EVERTims client. Eventually trace rays received from EVERTims
    client (for debug purpose).
    """

    def __init__(self):
        """
        EVERTims class constructor
        """

        # parent constructor
        super().__init__()

        # define locals
        self.drawRays = False
        self.bpy_handle_callback = None
        self.limit_update_room_update_timer = 0
        self.rooms = dict()
        self.sources = dict()        
        self.listeners = dict()

        # init OSC client (sender)
        self.oscClient = OSC.OSCClient()


    def setup(self, config):
        
        objects = bpy.context.scene.objects

        # debug
        self.dbg = config.debug_logs

        # clear locals
        self.clear()

        # get rooms
        roomGroupName = config.room_object
        kxObjList = bpy.data.groups[roomGroupName].objects
        self.rooms[roomGroupName] = EvertRoom(kxObjList)

        # get sources
        kxObj = objects.get(config.source_object)
        self.sources[kxObj.name] = EvertSourceListener(kxObj, 'source')

        # get listeners
        kxObj = objects.get(config.listener_object)
        self.listeners[kxObj.name] = EvertSourceListener(kxObj, 'listener')

        # get engine config
        self.engineType = config.engine_type
        self.ismMaxOrder = config.ism_max_order
        self.airAbsorption = config.air_absorption
        self.soundVelocity = config.sound_velocity

        # get network config
        self.initOsc(config.ip_remote, config.port_write)

        # drawer
        self.drawRays = config.draw_rays
        self.drawOrderMax = config.draw_order_max

        # init ray tracer
        if( self.drawRays ):
            # init ray manager
            self.rayManager = RayManager( (config.ip_local, config.port_read) )
            self.rayManager.dbg = config.debug_logs
            self.rayManager.drawOrderMax = config.draw_order_max

        # setup sub
        for obj in self.sources.values():
            obj.id = 1
            obj.dbg = config.debug_logs
            obj.initOsc(config.ip_remote, config.port_write)
            obj.setMoveThreshold(config.update_thresh_loc, config.update_thresh_rot)

        for obj in self.listeners.values():
            obj.id = 1
            obj.dbg = config.debug_logs
            obj.initOsc(config.ip_remote, config.port_write)
            obj.setMoveThreshold(config.update_thresh_loc, config.update_thresh_rot)

        for obj in self.rooms.values():
            obj.id = 1
            obj.dbg = config.debug_logs
            obj.initOsc(config.ip_remote, config.port_write)

        # debug
        if self.dbg: print('setup evertims complete')

    def clear(self):

        self.rooms.clear()
        self.sources.clear()
        self.listeners.clear()

    def start(self):

        # debug
        if self.dbg: print('evertims start')

        # start ray tracer (must start before the others to miss nothing)
        if( self.drawRays ):
            self.rayManager.start()

        # start client
        self.send('dsp', 1)
        self.send('order', self.ismMaxOrder)
        self.send('air', int(self.airAbsorption))
        self.send('soundvelocity', self.soundVelocity)

        # start sub
        for obj in self.sources.values(): obj.start()
        for obj in self.listeners.values(): obj.start()
        for obj in self.rooms.values(): obj.start()

    def stop(self):

        # stop client
        self.send('dsp', 0)

        # stop sub
        for obj in self.sources.values(): obj.stop()
        for obj in self.listeners.values(): obj.stop()
        for obj in self.rooms.values(): obj.stop()
        
        # stop ray tracer
        if( self.drawRays ):
            self.rayManager.stop()

    def update(self, objType = ''):
        """
        Upload Room, Source, and Listener information to EVERTims client.

        :param objType: which type of object to update: either 'room', 'source', 'listener', or 'mobile' (i.e. 'source' and 'listener')
        :type objType: String
        """

        # update sources
        for obj in self.sources.values():
            obj.update()

        # update listeners
        for obj in self.listeners.values():
            obj.update()

        # update listeners
        for obj in self.rooms.values():
            obj.update()

        # update ray tracer
        if( self.drawRays ):
            self.rayManager.update()

    def exportSceneAsOscList(self, config):

        from types import MethodType

        # define file path local (can't make it global because of weird bpy behavior)
        filePath = bpy.path.abspath("//evert-export.txt")

        # clear file
        f = open(filePath,"w+")
        f.write('')
        f.close

        # init
        self.setup(config)

        # save state
        drawRays = self.drawRays
        self.drawRays = False

        # swicth osc callbacks to write to disk. using MethodType allows to keep passing "self" (really bounding method) to method 
        # when invoking it
        self.send = MethodType(sendToDisk, self)
        for obj in self.rooms.values(): obj.send = MethodType(sendToDisk, obj)
        for obj in self.sources.values(): obj.send = MethodType(sendToDisk, obj)
        for obj in self.listeners.values(): obj.send = MethodType(sendToDisk, obj)

        # run full sequence
        self.start()
        self.update()
        self.stop()

        # restore config
        self.drawRays = drawRays

def sendToDisk(self, header, content = None):

    # define file path local (can't make it global because of weird bpy behavior)
    filePath = bpy.path.abspath("//evert-export.txt")

    # open (create if doesn't exist) file
    f = open(filePath,"a")

    # create header
    header = self.getOscHeader() + "/" + header

    # filter message list 
    discardList = ['dsp', 'destroy']
    if( any(s in header for s in discardList) ):
        return 

    # shape message
    if( content == None ):
        msg = header
    else:
        # shape content (e.g. tuple to string)
        if( isinstance(content, list) or isinstance(content, tuple) ):
            contentStr = ''
            for i in range(len(content)):
                contentStr = contentStr + ' ' + str(round(content[i],4)) # avoid outputs like 1e-6
        else:
            contentStr = str(content)
        msg = header + ' ' + contentStr

    # write to file
    f.write(msg + "\n")

    # close file
    f.close() 

    # def crystalizeVisibleRays(self):
    #     """
    #     Create a curve for all currently visible rays that will remain in the scene after the simulation is over
    #     """

    #     if self.rayManager: self.rayManager.crystalizeVisibleRays()
