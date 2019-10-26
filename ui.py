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
        box.label("Network", icon='URL')

        rowsub = box.row(align=True)
        rowsub.label("Evertims client IP adress & port:")
        rowsub = box.row(align=True)
        split = rowsub.split(percentage=0.6)
        colsub = split.column()
        colsub.prop(evertims, "ip_remote", text="")
        colsub = split.column()
        colsub.prop(evertims, "port_write", text="port")

        rowsub = box.row(align=True)
        split = rowsub.split(percentage=0.6)
        colsub = split.column()
        colsub.prop(evertims, "ip_local", text="")
        colsub = split.column()
        colsub.prop(evertims, "port_read", text="port")

        rowsub = box.row(align=True)
        if evertims.is_client_connected:
            rowsub.label("client detected")
        else:
            rowsub.label("client not detected")

        # Engine configuration
        box = layout.box()
        box.label("Engine configuration", icon='LAMP_AREA')
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "engine_type", expand=True)
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "ism_max_order", text="max order")
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
        rowsub.prop(addon_prefs, "material_file_path", text="mat file")
        rowsub = box.row(align=True)
        rowsub.operator("evert.import", text="refresh materials", icon="NONE").arg ='materials'

        # Drawer configuration
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "draw_rays", text="draw rays in 3D view")
        rowsub = box.row(align=True)
        rowsub.prop(evertims, "draw_order_max", text="max order")

        rowsub = box.row(align=True)
        rowsub.prop(evertims, "debug_logs", text="print logs to console")
        rowsub = box.row(align=True)
        if not evertims.enable_auralization:
            rowsub.operator("evert.run", text="START", icon="RADIOBUT_OFF").arg ='start'
        else:
            rowsub.operator("evert.run", text="STOP", icon="REC").arg ='stop'

        # Exporter
        # rowsub = box.row(align=True)
        # rowsub.operator("evert.export", text="Export", icon="TEXT").arg =''
        # rowsub = box.row(align=True)
        # rowsub.operator("evert.crystalize", text="Crystalize visible rays", icon="HAIR").arg =''


        # Import elements
        box = layout.box()
        box.label("Import elements", icon='GROUP')
        # rowsub = box.row(align=True)
        # rowsub.operator("evert.import_template", text="Template scene", icon='MESH_CUBE').arg = 'scene'

        # Define KX_GameObjects as EVERTims elements
        box = layout.box()
        box.label("Define as Evertims element", icon='PINNED')        
        col = box.column(align=True)
        col.prop_search(evertims, "room_object", bpy.data, "objects")
        col = box.column(align=True)
        col.prop_search(evertims, "listener_object", bpy.data, "objects")
        col = box.column(align=True)
        col.prop_search(evertims, "source_object", bpy.data, "objects")


# ############################################################
# Register / Unregister
# ############################################################


def register():
    bpy.utils.register_class(EvertimsToolBar)

def unregister():
    bpy.utils.unregister_class(EvertimsToolBar)
