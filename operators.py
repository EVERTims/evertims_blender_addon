import json
import bpy
import os
import random
from bpy.types import Operator
from . import utils
from .evertims import ( Evertims )


# ############################################################
# Methods triggered from UI
# ############################################################


# start / stop main auralization
class EvertimsRun(Operator):
    
    # header
    bl_label = "run auralization"
    bl_idname = 'evert.run'
    bl_options = {'REGISTER'}

    # shape input argument
    arg = bpy.props.StringProperty()

    # init locals
    _evertims = Evertims()
    _handle_timer = None

    # add local callback to blender stack
    @staticmethod
    def handle_add(self, context):

        # add local modal to blender callback stack (will call self.modal method from now on)
        context.window_manager.modal_handler_add(self)

        # setup timer to force modal callback execution more often than blender's default
        EvertimsRun._handle_timer = context.window_manager.event_timer_add(0.075, context.window)

        # debug
        if context.scene.evertims.debug_logs: print(__name__, 'added evertims callback to draw_handler')

    # remove local callback from blender stack
    @staticmethod
    def handle_remove(context):

        # check that handle_add has been called before
        if EvertimsRun._handle_timer is not None:

            # remove timer callback setup in handle_add
            context.window_manager.event_timer_remove(EvertimsRun._handle_timer)

            # reset locals
            EvertimsRun._handle_timer = None

            # debug
            if context.scene.evertims.debug_logs: print(__name__, 'removed evertims callback from draw_handler')

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    # method called from UI
    def invoke(self, context, event):

        # init locals
        scene = context.scene
        evertims = scene.evertims
        addon_prefs = context.user_preferences.addons[__package__].preferences

        # start auralization
        if self.arg == 'start':

            # sanity check: room defined
            if not evertims.room_object:
                self.report({'ERROR'}, 'No room defined')
                return {'CANCELLED'}

            # sanity check: source defined
            if not evertims.source_object:
                self.report({'ERROR'}, 'No source defined')
                return {'CANCELLED'}

            # sanity check: listener defined
            if not evertims.listener_object:
                self.report({'ERROR'}, 'No listener defined')
                return {'CANCELLED'}

            # sanity check: room materials are acoustic materials
            if not evertims.materials:

                # load material file if path defined
                if addon_prefs.material_file_path:
                    filePath = bpy.path.abspath(addon_prefs.material_file_path)
                    matDict = utils.loadMaterialFile(filePath)
                    evertims.materials = utils.dict2str(matDict)
                
                # throw error otherwise
                else:
                    self.report({'ERROR'}, 'undefined material file path')
                    return {'CANCELLED'}

            # sanity check: all objects in room group have acoustic materials
            roomObjects = bpy.data.groups[evertims.room_object].objects
            for obj in roomObjects:

                # get object materials
                materialSlots = obj.material_slots

                # abort if no material defined
                if( len( materialSlots ) == 0 ):
                    self.report({'ERROR'}, 'room object ' + obj.name +' has no material')
                    return {'CANCELLED'}

                # get list of acoustic materials
                matDict = utils.str2dict(evertims.materials)

                # loop over materials in object, check if member of acoustic materials 
                for mat in materialSlots:
                    if not mat.name in matDict:
                        self.report({'ERROR'}, 'room object ' + obj.name +' material ' + mat.name + ': not an acoustic material')
                        return {'CANCELLED'}

            # pass parameters to evertims
            self._evertims.setup(evertims)

            # start evertims
            self._evertims.start()

            # flag auralization on
            evertims.enable_auralization = True

            # add local callback to blender stack
            self.handle_add(self,context)

            return {'RUNNING_MODAL'}

        # stop auralization
        elif self.arg == 'stop':

            # flag auralization off
            evertims.enable_auralization = False

            return {'FINISHED'}

        # crystalize visible rays
        elif self.arg == 'crystalize':

            self._evertims.crystalizeVisibleRays()
            
            return {'FINISHED'}


    # local modal callback (run always)
    def modal(self, context, event):

        # init locals
        scene = context.scene
        evertims = scene.evertims

        # auralization stop flagged: kill modal
        if not evertims.enable_auralization:
            self.cancel(context)
            return {'CANCELLED'}

        # execute modal on timer event
        elif event.type == 'TIMER':

            # execute evertims internal callback
            self._evertims.update()
            
            # force bgl rays redraw (else only redraw rays on user input event)
            if not context.area is None:
                context.area.tag_redraw()

        return {'PASS_THROUGH'}

    # modal cancel method, called (when modal enabled) when blender quit or load new scene
    def cancel(self, context):
        
        # remove local callback
        self.handle_remove(context)
        
        # remove nested callback
        self._evertims.stop()

        # force redraw to clean scene of rays
        if not context.area is None: 
            context.area.tag_redraw()


# import materials
class EvertimsImport(Operator):

    # header
    bl_label = "various import operations"
    bl_idname = 'evert.import'
    bl_options = {'REGISTER'}

    # shape input arguments
    arg = bpy.props.StringProperty()

    # method called from UI
    def execute(self, context):

        # init locals
        evertims = context.scene.evertims
        addon_prefs = context.user_preferences.addons[__package__].preferences

        # import materials
        if self.arg == 'materials':

            # check if material path defined
            if not addon_prefs.material_file_path:
                self.report({'ERROR'}, 'undefined material file path')
                return {'CANCELLED'}
            
            # load material list from file
            filePath = bpy.path.abspath(addon_prefs.material_file_path)
            matDict = utils.loadMaterialFile(filePath)

            # create materials if need be
            existingMatNameList = [x.name for x in bpy.data.materials]
            for matName in matDict:
                if( matName not in existingMatNameList ):
                    bpy.data.materials.new(name=matName)
                    bpy.data.materials[matName].diffuse_color = (random.random(), random.random(), random.random())

            # save material list to locals
            evertims.materials = utils.dict2str(matDict)

        return {'FINISHED'}


# export scene to disk
class EvertimsExport(Operator):
    
    # header
    bl_label = "export scene"
    bl_idname = 'evert.export'
    bl_options = {'REGISTER'}

    # method called from UI
    def execute(self, context):

        # init locals
        evertims = context.scene.evertims
        _evertims = Evertims()

        # export scene to disk
        _evertims.exportSceneAsOscList(evertims)

        return {'FINISHED'}


# ############################################################
# Register / Unregister
# ############################################################


classes = (
    EvertimsRun, 
    EvertimsExport, 
    EvertimsImport
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
