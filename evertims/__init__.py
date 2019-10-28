import bpy
from types import MethodType
from .evertClass import *
from . import OSC


# ############################################################
# Main Evertims python module 
# ############################################################


# Core of the Evertims add-on, handle calls from UI, create and control Evertims objects
class Evertims(AbstractOscSender):


    def __init__(self):

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


    # get current configuration from UI 
    def setup(self, config):
        
        # init locals
        objects = bpy.context.scene.objects
        self.clear()

        # save general config to locals
        self.dbg = config.debug_logs
        self.engineType = config.engine_type
        self.ismMaxOrder = config.ism_max_order
        self.airAbsorption = config.air_absorption
        self.soundVelocity = config.sound_velocity
        self.drawRays = config.draw_rays
        self.drawOrderMax = config.draw_order_max

        # init local OSC sender
        self.initOsc(config.ip_remote, config.port_write)

        # init ray manager
        if( self.drawRays ):
            self.rayManager = RayManager( (config.ip_local, config.port_read) )
            self.rayManager.dbg = self.dbg
            self.rayManager.drawOrderMax = self.drawOrderMax

        # init scene objects: rooms
        roomGroupName = config.room_object
        kxObjList = bpy.data.groups[roomGroupName].objects
        self.rooms[roomGroupName] = EvertRoom(kxObjList)

        # init scene objects: sources
        kxObj = objects.get(config.source_object)
        self.sources[kxObj.name] = EvertSourceListener(kxObj, 'source')

        # init scene objects: listeners
        kxObj = objects.get(config.listener_object)
        self.listeners[kxObj.name] = EvertSourceListener(kxObj, 'listener')

        # setup scene objects: sources
        for obj in self.sources.values():
            obj.id = 1
            obj.dbg = self.dbg
            obj.initOsc(config.ip_remote, config.port_write)
            obj.setMoveThreshold(config.update_thresh_loc, config.update_thresh_rot)

        for obj in self.listeners.values():
            obj.id = 1
            obj.dbg = self.dbg
            obj.initOsc(config.ip_remote, config.port_write)
            obj.setMoveThreshold(config.update_thresh_loc, config.update_thresh_rot)

        for obj in self.rooms.values():
            obj.id = 1
            obj.dbg = self.dbg
            obj.initOsc(config.ip_remote, config.port_write)
            obj.udpateInterval = config.update_thresh_time

        # debug
        if self.dbg: print(__name__, 'setup complete')


    # clear local dict (room, source, listener)
    def clear(self):

        self.rooms.clear()
        self.sources.clear()
        self.listeners.clear()


    # start auralization
    def start(self):

        # debug
        if( self.dbg ): print(__name__, 'start auralization')

        # start ray tracer (before any other not to miss any incomming packet)
        if( self.drawRays ): self.rayManager.start()

        # start client
        self.send('dsp', 1)

        # pass engine config to client
        self.send('order', self.ismMaxOrder)
        self.send('air', int(self.airAbsorption))
        self.send('soundvelocity', self.soundVelocity)

        # start sources, rooms, and listeners
        for obj in self.sources.values(): obj.start()
        for obj in self.listeners.values(): obj.start()
        for obj in self.rooms.values(): obj.start()


    # stop auralization
    def stop(self):

        # debug
        if( self.dbg ): print(__name__, 'stop auralization')

        # stop client
        self.send('dsp', 0)

        # stop sources, rooms, and listeners
        for obj in self.sources.values(): obj.stop()
        for obj in self.listeners.values(): obj.stop()
        for obj in self.rooms.values(): obj.stop()
        
        # stop ray tracer
        if( self.drawRays ): self.rayManager.stop()


    # running callback
    def update(self):
        
        # update sources, rooms, and listeners
        for obj in self.sources.values(): obj.update()
        for obj in self.listeners.values(): obj.update()
        for obj in self.rooms.values(): obj.update()

        # update ray tracer
        if( self.drawRays ): self.rayManager.update()


    # export scene to disk as list of osc messages
    def exportSceneAsOscList(self, config):

        # define file path local (can't make it global because of weird bpy behavior)
        filePath = bpy.path.abspath("//evert-export.txt")

        # create/clear file
        f = open(filePath,"w+")
        f.write('')
        f.close

        # init
        self.setup(config)

        # prevent ray drawing: save draw state, set to false
        drawRays = self.drawRays
        self.drawRays = False

        # switch osc send callbacks to write to disk. using "MethodType" truly bounds 
        # the method to the class, i.e. passing it "self" upon execution 
        self.send = MethodType(sendToDisk, self)
        for obj in self.rooms.values(): obj.send = MethodType(sendToDisk, obj)
        for obj in self.sources.values(): obj.send = MethodType(sendToDisk, obj)
        for obj in self.listeners.values(): obj.send = MethodType(sendToDisk, obj)

        # run full auralization sequence
        self.start()
        self.update()
        self.stop()

        # restore config
        self.drawRays = drawRays


    # Create a curve for all currently visible rays that will remain in the scene after 
    # the simulation is over
    def crystalizeVisibleRays(self):
        if self.rayManager: self.rayManager.crystalizeVisibleRays()
    

# method replacing the "send" method of all AbstractOscSenders, writing to disk instead
# of sending OSC message
def sendToDisk(self, header, content = None):

    # define file path local (can't make it global because of weird bpy behavior)
    filePath = bpy.path.abspath("//evert-export.txt")

    # open file
    f = open(filePath,"a")

    # create header
    header = self.getOscHeader() + "/" + header

    # filter message list (only interested in spat5.evert messages, not those that control
    # the rest of the client behavior)
    discardList = ['dsp', 'destroy']
    if( any(s in header for s in discardList) ): return 

    # shape message
    if( content == None ):
        msg = header

    else:
        
        # shape content in case of tuple or list
        if( isinstance(content, list) or isinstance(content, tuple) ):
            contentStr = ''
            for i in range(len(content)):
                contentStr = contentStr + ' ' + str(round(content[i],4)) # avoid outputs like 1e-6
        
        # default shape content
        else:
            contentStr = str(content)
        
        msg = header + ' ' + contentStr

    # write to file
    f.write(msg + "\n")

    # close file
    f.close()
