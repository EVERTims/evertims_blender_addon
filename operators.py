import json
import bpy
import os
import random
from bpy.types import Operator
from . import utils
from .evertims import ( Evertims )


class EvertimsRun(Operator):
    """Run auralization"""
    bl_label = "run auralization"
    bl_idname = 'evert.run'
    bl_options = {'REGISTER', 'UNDO'}

    arg = bpy.props.StringProperty()

    _evertims = Evertims()
    _handle_timer = None

    @staticmethod
    def handle_add(self, context):
        # EvertimsRun._handle_draw_callback = bpy.types.SpaceView3D.draw_handler_add(EvertimsRun._draw_callback, (self,context), 'WINDOW', 'PRE_VIEW')
        context.window_manager.modal_handler_add(self)
        EvertimsRun._handle_timer = context.window_manager.event_timer_add(0.075, context.window)
        if context.scene.evertims.debug_logs: print('added evertims callback to draw_handler')

    @staticmethod
    def handle_remove(context):
        if EvertimsRun._handle_timer is not None:
            context.window_manager.event_timer_remove(EvertimsRun._handle_timer)
            EvertimsRun._handle_timer = None
            # context.window_manager.modal_handler_add(self)
            # bpy.types.SpaceView3D.draw_handler_remove(EvertimsRun._handle_draw_callback, 'WINDOW')
            # EvertimsRun._handle_draw_callback = None
            if context.scene.evertims.debug_logs: print('removed evertims callback from draw_handler')

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):

        scene = context.scene
        evertims = scene.evertims
        addon_prefs = context.user_preferences.addons[__package__].preferences

        # get active object
        # obj = bpy.context.scene.objects.active

        if self.arg == 'start':

            # sanity check: room defined
            if not evertims.room_object:
                self.report({'ERROR'}, 'No room selected')
                return {'CANCELLED'}

            # sanity check: source defined
            if not evertims.source_object:
                self.report({'ERROR'}, 'No source selected')
                return {'CANCELLED'}

            # sanity check: listener defined
            if not evertims.listener_object:
                self.report({'ERROR'}, 'No listener selected')
                return {'CANCELLED'}

            # sanity check: room materials are acoustic materials
            if not evertims.materials:

                # load material file if need be

                if not addon_prefs.material_file_path:
                    self.report({'ERROR'}, 'undefined material file path')
                    return {'CANCELLED'}
                else:
                    # load material list from file
                    filePath = bpy.path.abspath(addon_prefs.material_file_path)
                    matDict = utils.loadMaterialFile(filePath)
                    evertims.materials = utils.dict2str(matDict)

            # check room materials are acoustic materials
            objects = bpy.context.scene.objects
            room = objects.get(evertims.room_object)
            materialSlots = room.material_slots
            matDict = utils.str2dict(evertims.materials)
            for mat in materialSlots:
                if not mat.name in matDict:
                    self.report({'ERROR'}, 'room ' + room.name + ' material ' + mat.name + ': not an acoustic material')
                    return {'CANCELLED'}

            # pass parameters to evertims
            self._evertims.setup(evertims)

            # flag auralization on
            evertims.enable_auralization = True

            # add callback
            self.handle_add(self,context)

            return {'RUNNING_MODAL'}


        elif self.arg == 'stop':

            evertims.enable_auralization = False
            return {'FINISHED'}

    def modal(self, context, event):
        """
        modal method, run always, call cancel function when Blender quit / load new scene
        """

        scene = context.scene
        evertims = scene.evertims

        # kill modal
        if not evertims.enable_auralization:
            self.cancel(context)

            # return flag to notify callback manager that this callback is no longer running
            return {'CANCELLED'}

        # execute modal
        elif event.type == 'TIMER':

            # run evertims internal callbacks
            self._evertims.update()
            
            # force bgl rays redraw (else only redraw rays on user input event)
            if not context.area is None:
                context.area.tag_redraw()

        return {'PASS_THROUGH'}


    def cancel(self, context):
        """
        called when Blender quit / load new scene. Remove local callback from stack
        """
        # remove local callback
        self.handle_remove(context)
        
        # remove nested callback
        self._evertims.stop()

        # erase rays from screen
        if not context.area is None: 
            context.area.tag_redraw()


class EvertimsImport(Operator):
    """Import misc."""
    bl_label = "various import operations"
    bl_idname = 'evert.import'
    bl_options = {'REGISTER', 'UNDO'}

    arg = bpy.props.StringProperty()

    def execute(self, context):

        evertims = context.scene.evertims
        addon_prefs = context.user_preferences.addons[__package__].preferences

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

            # save locals
            evertims.materials = utils.dict2str(matDict)

        return {'FINISHED'}





class EvertimsExport(Operator):
    """Export scene elements"""
    bl_label = "export scene"
    bl_idname = 'evert.export'
    bl_options = {'REGISTER', 'UNDO'}


classes = (
    EvertimsRun, 
    EvertimsExport, 
    EvertimsImport
    )


# ############################################################
# Register / Unregister
# ############################################################


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
