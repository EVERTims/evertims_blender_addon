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
    bl_idname = 'evertims.run'
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

            # check scene integrity
            (status, msg) = utils.checkSceneIntegrity(context, evertims)
            if status != {'PASS'}:
                self.report(status, msg)
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
    bl_idname = 'evertims.import'
    bl_options = {'REGISTER'}

    # shape input arguments
    arg = bpy.props.StringProperty()

    # method called from UI
    def execute(self, context):

        # init locals
        evertims = context.scene.evertims

        # import materials
        if self.arg == 'materials':

            # forced refresh
            (status, msg) = utils.loadMaterials(context, evertims, True)
            if status != {'PASS'}:
                self.report(status, msg)
                return {'CANCELLED'}

            # convert local string to dict
            matDict = utils.str2matDict(evertims.materials)

            # create materials if need be
            existingMatNameList = [x.name for x in bpy.data.materials]
            for matName in matDict:
                if( matName not in existingMatNameList ):
                    bpy.data.materials.new(name=matName)
                    bpy.data.materials[matName].diffuse_color = (random.random(), random.random(), random.random())

        return {'FINISHED'}


# export scene to disk
class EvertimsExport(Operator):
    
    # header
    bl_label = "export scene"
    bl_idname = 'evertims.export'
    bl_options = {'REGISTER'}

    # method called from UI
    def execute(self, context):

        # init locals
        evertims = context.scene.evertims
        _evertims = Evertims()

        # check scene integrity
        (status, msg) = utils.checkSceneIntegrity(context, evertims)
        if status != {'PASS'}:
            self.report(status, msg)
            return {'CANCELLED'}

        # check export file name
        filePath = bpy.path.abspath(evertims.export_file_path)
        (status, msg) = utils.isValidExportPath(filePath)
        if status != {'PASS'}:
            self.report(status, msg)
            return {'CANCELLED'}

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
