import bpy
import bpy.utils.previews
import os
from bpy.types import Panel


# ############################################################
# User interface definition
# ############################################################


class EvertimsUIBase:
    bl_category = "Evertims"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        return True


class VIEW3D_PT_EvertimsToolBar(EvertimsUIBase, Panel):

    bl_label = "Evertims"

    def draw(self, context):

        # get locals
        layout = self.layout
        scene = context.scene
        evertims = scene.evertims
        addon_prefs = context.preferences.addons[__package__].preferences

        # Network configuration
        box = layout.box()
        box.enabled = not evertims.enable_auralization
        box.label(text="Network", icon='URL')
        #
        rowsub = box.row(align=True)
        rowsub.label(text="Remote Address")
        rowsub = box.row(align=True)
        split = rowsub.split(factor=0.6)
        colsub = split.column()
        colsub.prop(evertims, "ip_remote", text="")
        colsub = split.column()
        colsub.prop(evertims, "port_write", text="")
        #
        rowsub = box.row(align=True)
        rowsub.label(text="Local Address")
        rowsub = box.row(align=True)
        split = rowsub.split(factor=0.6)
        colsub = split.column()
        colsub.prop(evertims, "ip_local", text="")
        colsub = split.column()
        colsub.prop(evertims, "port_read", text="")

        # Engine configuration
        box = layout.box()
        box.enabled = not evertims.enable_auralization
        box.label(text="Engine Configuration", icon='PREFERENCES')
        #
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "engine_type", expand=False)
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "ism_max_order", text="Order Max")
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "sound_velocity", text="Sound Velocity (m/s)")
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "air_absorption", text="Air Absorption")
        #
        rowsub = box.row(align=True)
        rowsub.label(text="Update Throttle:")
        rowsub = box.row(align=True)
        split = rowsub.split(factor=0.5)
        colsub = split.column()
        colsub.prop(evertims, "update_thresh_loc", text="Loc (m)")
        colsub = split.column()
        colsub.prop(evertims, "update_thresh_rot", text="Rot (deg)")
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "update_thresh_time", text="Time (sec)")
        #
        rowsub = box.row(align=True)
        rowsub.prop(addon_prefs, "material_file_path", text="Material File")
        rowsub = box.row(align=True)
        rowsub.operator("evertims.import", text="Import Materials", icon="IMPORT").arg = 'materials'

        # Import elements
        # box = layout.box()
        # box.label(text="Import elements", icon='GROUP')
        # rowsub = box.row(align=True)
        # rowsub.operator("evertims.import_template", text="Template scene", icon='MESH_CUBE').arg = 'scene'

        # Define scene objects as evertims elements
        box = layout.box()
        box.enabled = not evertims.enable_auralization
        box.label(text="Scene Components", icon='SCENE_DATA')
        #
        col = box.column(align=True)
        col.prop_search(evertims, "room_group", bpy.data, "collections")
        col = box.column(align=True)
        col.prop_search(evertims, "listener_object", bpy.data, "objects")
        col = box.column(align=True)
        col.prop_search(evertims, "source_object", bpy.data, "objects")

        # Source directivity
        self.drawSourceDirectivity(context)

        # Auralization run
        box = layout.box()
        box.label(text="Auralization", icon='PARTICLE_DATA')
        #
        rowsub = box.row(align=True)
        rowsub.enabled = not evertims.enable_auralization
        split = rowsub.split(factor=0.5)
        colsub = split.column()
        colsub.prop(evertims, "draw_rays", text="Draw Paths")
        colsub = split.column()
        colsub.prop(evertims, "draw_order_max", text="Draw Order Max")
        colsub.enabled = not evertims.enable_auralization
        #
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "debug_logs", text="Print Logs To Console")
        rowsub.enabled = not evertims.enable_auralization
        #
        rowsub = box.row(align=True)
        rowsub.alignment = 'CENTER'
        rowsub.label(text="(Avoid using undo during auralization)")
        rowsub = box.row(align=True)
        if not evertims.enable_auralization:
            rowsub.operator("evertims.run", text="Start", icon="RADIOBUT_OFF").arg = 'start'
        else:
            rowsub.operator("evertims.run", text="Stop", icon="REC").arg = 'stop'

        # Exporter
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        #
        # export scene to disk (.txt) as list of osc messages
        rowsub = box.row(align=True)
        rowsub.enabled = not evertims.enable_auralization
        rowsub.prop(evertims, "export_file_path", text="Export File")
        rowsub = box.row(align=True)
        rowsub.enabled = not evertims.enable_auralization
        rowsub.operator("evertims.export", text="Export Scene To Disk", icon="EXPORT")
        # crystalize acoustic rays in scene as curves
        rowsub = box.row(align=True)
        rowsub.enabled = evertims.enable_auralization
        rowsub.operator("evertims.run", text="Solidify Visible Paths", icon="STRANDS").arg = 'solidify'


    def drawSourceDirectivity(self, context):

        # get locals
        layout = self.layout
        scene = context.scene
        evertims = scene.evertims

        # header
        box = layout.box()
        box.enabled = not evertims.enable_auralization
        box.label(text="Source directivity", icon='MOD_CAST')

        # add umenu to directivity type enum
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "source_directivity_type", expand=False, text="Type")

        # discard if source directivity disabled
        if evertims.source_directivity_type == "disabled":
            return

        # # display directivity values (all vector at once)
        # colsub = box.column(align=True)
        # colsub.prop(evertims, "source_directivity_values", text="Selectivity coefficients")

        # display directivity values (with freq values beside)
        colsub = box.column(align=True)
        for iFreq in range(0, len(evertims.source_directivity_frequencies)):

            # get freq string (Hz / kHz)
            freq = evertims.source_directivity_frequencies[iFreq]
            if( freq >= 1000 ): freq = str(round(freq/1000)) + "kHz"
            else: freq = str(freq) + "Hz"

            # create new row, populate it
            rowsub = colsub.row(align=True)
            rowsub.label(text=freq)
            rowsub.prop(evertims, 'source_directivity_values', index = iFreq, text="")


# ############################################################
# Register / Unregister
# ############################################################


def register():
    bpy.utils.register_class(VIEW3D_PT_EvertimsToolBar)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_EvertimsToolBar)
