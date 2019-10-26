from . import ( OSC, evertUtils )

class AbstractBase():

    def __init__(self):
        self.dbg = False

class AbstractOscSender(AbstractBase):

    def __init__(self):

        # parent constructor
        super().__init__()

        self.osc = {
        'header': "",
        'client': OSC.OSCClient(), 
        'ip_remote': None,
        'port_write': None
        }

    def initOsc(self, ip, port):

        self.osc['ip_remote'] = ip
        self.osc['port_write'] = port

    def getIdAsString(self):
        return ""

    def getOscHeader(self):
        # shape empty header if oscHeader empty
        if (self.osc['header'] == ""):
            return ""

        # shape header without id if not defined
        if( self.getIdAsString () == "" ):
            return "/" + self.osc['header']
        
        # default
        return "/" + self.osc['header'] + "/" + self.getIdAsString ()

    def send(self, header, content = None):
        """ Send OSC message """
        
        # init locals
        ip = self.osc['ip_remote']
        port = self.osc['port_write']

        # sanity check
        if( not ip or not port ):
            print('!!! need to define ip and port in osc sender ' + __name__)
            return 

        # create header
        header = self.getOscHeader() + "/" + header

        # create OSC message, set address, fill message
        msg = OSC.OSCMessage()
        msg.setAddress(header)
        if( content ): msg.append(content)

        # send OSC message
        try:
            self.osc['client'].sendto(msg,(ip, port))
            if self.dbg: print ('-> sent to ' + str(port) + '@' + ip + ': ' + header, content)
        except TypeError:
            print ('!!! no route to', port, ip, 'to send OSC message:', header.split(' ')[0]) # may occur in OSC.py if no route to host


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
        self.send("destroy")


class AbstractMovable(AbstractObj):

    def __init__(self):

        # parent constructor
        super().__init__()

        # locals
        self.moveThresholdLoc = 0.1
        self.moveThresholdRot = 1
        self.old_worldTransform = None
        
    def update(self):

        # discard if no need for update
        if not self.hasMoved():
            return 

        # shape transform message content
        world_tranform = self.obj.matrix_world
        mat = evertUtils.mat4x4ToTuple(world_tranform)

        # send msg
        self.send("transform/matrix", mat)
        

    def setMoveThreshold(self, thresholdLoc, thresholdRot):
        """
        Define a threshold value to limit listener / source update to EVERTims client.

        :param threshold: value above which an EVERTims object as to move to be updated (in position) to the client
        :type threshold: Float
        """
        self.moveThresholdLoc = thresholdLoc
        self.moveThresholdRot = thresholdRot

    def hasMoved(self):
        """
        Check if source/client has moved since last check.

        :return: a boolean saying whether or not the source / listener moved since last check
        :rtype: Boolean
        """
        
        world_tranform = self.obj.matrix_world.copy()

        # if objed has not yet been checked
        if not self.old_worldTransform:
            self.old_worldTransform = world_tranform
            return True

        elif evertUtils.areDifferent_Mat44(world_tranform, self.old_worldTransform, self.moveThresholdLoc, self.moveThresholdRot):
            # moved since last check
            self.old_worldTransform = world_tranform
            return True
        else:
            # did not move since last check
            return False






