import bpy
import bpy.utils.previews
import os
from bpy.types import Panel

# ############################################################
# User Interface
# ############################################################

class EvertimsUIBase:
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_description= ""
    bl_category = "Evertims"

class EvertimsToolBar(EvertimsUIBase, Panel):

    bl_label = "Evertims"

    @staticmethod

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        evertims = scene.evertims
        addon_prefs = context.user_preferences.addons[__package__].preferences
        # layout.enabled = True

        # Network configuration
        box = layout.box()
        box.enabled = not evertims.enable_auralization
        box.label("Network", icon='URL')

        rowsub = box.row(align=True)
        split = rowsub.split(percentage=0.6)
        colsub = split.column()
        colsub.prop(evertims, "ip_remote", text="ip remote")
        colsub = split.column()
        colsub.prop(evertims, "port_write", text="port write")

        rowsub = box.row(align=True)
        split = rowsub.split(percentage=0.6)
        colsub = split.column()
        colsub.prop(evertims, "ip_local", text="ip local")
        colsub = split.column()
        colsub.prop(evertims, "port_read", text="port read")

        # rowsub = box.row(align=True)
        # if evertims.is_client_connected:
        #     rowsub.label("client detected")
        # else:
        #     rowsub.label("client not detected")

        # Engine configuration
        box = layout.box()
        box.enabled = not evertims.enable_auralization
        box.label("Engine configuration", icon='PREFERENCES')

        rowsub = box.row(align=True)
        rowsub.prop(evertims, "engine_type", expand=False)
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "ism_max_order", text="ism order max")
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "sound_velocity", text="sound velocity (m/s)")
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "air_absorption", text="enable air absorption")
        rowsub = box.row(align=True)
        rowsub.label("Movement update threshold:")
        rowsub = box.row(align=True)
        split = rowsub.split(percentage=0.5)
        colsub = split.column()
        colsub.prop(evertims, "update_thresh_loc", text="loc (m)")
        colsub = split.column()
        colsub.prop(evertims, "update_thresh_rot", text="rot (deg)")
        rowsub = box.row(align=True)
        rowsub.prop(addon_prefs, "material_file_path", text="material file")
        rowsub = box.row(align=True)
        rowsub.operator("evert.import", text="Refresh Materials", icon="FILE_REFRESH").arg ='materials'

        # Import elements
        # box = layout.box()
        # box.label("Import elements", icon='GROUP')
        # rowsub = box.row(align=True)
        # rowsub.operator("evert.import_template", text="Template scene", icon='MESH_CUBE').arg = 'scene'

        # Define KX_GameObjects as EVERTims elements
        box = layout.box()
        box.enabled = not evertims.enable_auralization
        box.label("Define as Evertims element", icon='GROUP')

        col = box.column(align=True)
        col.prop_search(evertims, "room_object", bpy.data, "objects")
        col = box.column(align=True)
        col.prop_search(evertims, "listener_object", bpy.data, "objects")
        col = box.column(align=True)
        col.prop_search(evertims, "source_object", bpy.data, "objects")

        # Auralization run
        box = layout.box()
        box.label("Run auralization", icon='LAMP_AREA')

        rowsub = box.row(align=True)
        rowsub.enabled = not evertims.enable_auralization
        split = rowsub.split(percentage=0.5)
        colsub = split.column()
        colsub.prop(evertims, "draw_rays", text="draw paths")
        colsub = split.column()
        colsub.prop(evertims, "draw_order_max", text="draw order max")
        colsub.enabled = not evertims.enable_auralization

        rowsub = box.row(align=True)
        rowsub.prop(evertims, "debug_logs", text="print logs to console")
        rowsub.enabled = not evertims.enable_auralization
        rowsub = box.row(align=True)
        if not evertims.enable_auralization:
            rowsub.operator("evert.run", text="Start", icon="RADIOBUT_OFF").arg ='start'
        else:
            rowsub.operator("evert.run", text="Stop", icon="REC").arg ='stop'

        # Exporter
        # rowsub = box.row(align=True)
        # rowsub.operator("evert.export", text="Export", icon="TEXT").arg =''
        # rowsub = box.row(align=True)
        # rowsub.operator("evert.crystalize", text="Crystalize visible rays", icon="HAIR").arg =''


# ############################################################
# Register / Unregister
# ############################################################


def register():
    bpy.utils.register_class(EvertimsToolBar)

def unregister():
    bpy.utils.unregister_class(EvertimsToolBar)
