from . import ( OSC, evertUtils )


# ############################################################
# Abstract classes (to be inherited by Evertims classes)
# ############################################################

# base class
class AbstractBase():

    def __init__(self):
        self.dbg = False

# any object capable of sending OSC messages
class AbstractOscSender(AbstractBase):

    def __init__(self):

        # parent constructor
        super().__init__()

        # init local
        self.osc = {
        'header': "",
        'client': OSC.OSCClient(), 
        'ip_remote': None,
        'port_write': None
        }


    # setup osc parameters
    def initOsc(self, ip, port):

        self.osc['ip_remote'] = ip
        self.osc['port_write'] = port


    # get object id (added to osc messages)
    def getIdAsString(self):
        return ""


    # get object osc header (prepended to all its osc messages)
    def getOscHeader(self):

        # shape empty header if oscHeader empty
        if( self.osc['header'] == "" ): return ""

        # shape header without id if not defined
        if( self.getIdAsString () == "" ): return "/" + self.osc['header']
        
        # shape header with id
        return "/" + self.osc['header'] + "/" + self.getIdAsString ()

    # send osc message
    def send(self, header, content = None):
        
        # locals
        ip = self.osc['ip_remote']
        port = self.osc['port_write']

        # sanity check
        if( not ip or not port ):
            print(self.__class__.__name__, 'error: undefined osc sender ip and/or port')
            return 

        # prepend local header to msg header
        header = self.getOscHeader() + "/" + header

        # create OSC message
        msg = OSC.OSCMessage()
        msg.setAddress(header)
        if( content != None ): msg.append(content)

        # send OSC message
        try:
            self.osc['client'].sendto(msg,(ip, port))
            if self.dbg: print ('-> osc send to ' + str(port) + '@' + ip + ': ' + header, content)
        except TypeError:
            print ('error: osc message send fail: no route to', str(port) + '@' + ip)
            return


# any room, source, or listener
class AbstractObj(AbstractOscSender):

    def __init__(self):

        # parent constructor
        super().__init__()

        # init locals
        self.id = None
        self.obj = None

    def start(self):
        # notify client of object spawn
        self.send("spawn")

    def getIdAsString(self):
        return str(self.id)

    def stop(self):
        # notify client of object destroy
        self.send("destroy")


# any source, listener
class AbstractMovable(AbstractObj):

    def __init__(self):

        # parent constructor
        super().__init__()

        # locals
        self.moveThresholdLoc = 0.1
        self.moveThresholdRot = 1
        self.old_worldTransform = None
        
    # running callback
    def update(self):

        # discard if no need for update
        if( not self.hasMoved() ): return 

        # shape transform message content
        world_tranform = self.obj.matrix_world.normalized() # discard source / listener object scaling
        mat = evertUtils.mat4x4ToTuple(world_tranform)

        # send transform message
        self.send("transform/matrix", mat)
        
    # define threshold value to limit movable updates to Evertims client.
    def setMoveThreshold(self, thresholdLoc, thresholdRot):
        self.moveThresholdLoc = thresholdLoc
        self.moveThresholdRot = thresholdRot

    # check if movable has moved since last check
    def hasMoved(self):
        
        # get local copy of object transform        
        world_tranform = self.obj.matrix_world.copy()

        # first time: need update
        if not self.old_worldTransform:
            self.old_worldTransform = world_tranform
            return True

        # transform did change
        elif evertUtils.areDifferent_Mat44(world_tranform, self.old_worldTransform, self.moveThresholdLoc, self.moveThresholdRot):
            self.old_worldTransform = world_tranform
            return True
        
        # transform did not change
        else: return False
