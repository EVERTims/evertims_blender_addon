
bl_info = {
    "name": "Evertims real-time auralization",
    "author": "David Poirier-Quinot",
    "version": (1, 0, 0),
    "blender": (2, 93, 0),
    "location": "3D View > Sidebar",
    "description": "Real-time room acoustics in the viewport",
    "doc_url": "",
    "support": 'COMMUNITY',
    "category": "System",
}

if "bpy" in locals():
    import importlib
    importlib.reload(ui)
    importlib.reload(operators)
    importlib.reload(utils)
    if "evertims" in locals():
        importlib.reload(evertims)
    # importlib.reload(evertims)
else:
    import bpy
    from bpy.props import (
        StringProperty,
        EnumProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        IntVectorProperty,
        PointerProperty,
        CollectionProperty
        )
    from bpy.types import (
        PropertyGroup,
        AddonPreferences
        )
    from . import (
        ui,
        operators,
        # evertims
        )
    # import of the evertims module is not necessary here. Added for debug: reloading twice
    # the addon will now reload the content of the ./evertims module as well (at least its
    # __init__)


# ############################################################
# Add-on entry point + property definition
# ############################################################


class EvertimsSettings(PropertyGroup):

    # Network configuration
    ip_remote: StringProperty(
            name="IP remote",
            description="IP of the computer running the Evertims client",
            default="127.0.0.1", maxlen=1024,
            )
    ip_local: StringProperty(
            name="IP local",
            description="IP of the computer running Blender",
            default="127.0.0.1", maxlen=1024,
            )
    port_write: IntProperty(
            name="Port out",
            description="Port used by the Evertims client to read data sent by Blender",
            default=4002,
            )
    port_read: IntProperty(
            name="Port in",
            description="Port used by Blender to read data sent by the Evertims client",
            default=4001,
            )
    is_client_connected: BoolProperty(
            name="Is Evertims client connected",
            description="Set to true if connection to Evertims client can be established",
            default=False,
            )

    # Engine configuration
    engine_type: EnumProperty(
            name="Engine type",
            description="Current method selected to compute auralization",
            items={
            ("ISM", "Image Source", "Image Source Model")
            },
            default="ISM")
    sound_velocity: FloatProperty(
            name="Sound velocity",
            description="Travelling speed of sound during simulation",
            default=343.3, max=600, min=1
            )
    air_absorption: BoolProperty(
            name="Enable air absorption",
            description="Enable the frequency specific air absorption of acoustic energy during the simulation",
            default=True,
            )
    ism_max_order: IntProperty(
            name="Max ISM order",
            description="Maximum reflection order considered during the image source simulation",
            default=3, min=0, max=10
            )
    update_thresh_loc: FloatProperty(
            name="Update threshold location (m)",
            description="Minimum amount of translation required to trigger an update of a given source/listener location",
            default=0.1, min=0
            )
    update_thresh_rot: FloatProperty(
            name="Update threshold rotation (deg)",
            description="Minimum amount of rotation required to trigger an update of a given source/listener location",
            default=1, min=0, max=360
            )
    update_thresh_time: FloatProperty(
            name="Update threshold time (sec)",
            description="Minimum amount of time required between two room updates",
            default=1, min=0
            )

    # Drawer configuration
    draw_rays: BoolProperty(
            name="Draw Rays",
            description="Draw rays resulting from Evertims simulation in the 3D view",
            default=True,
            )
    draw_order_max: IntProperty(
            name="Max image source order drawn",
            description="Maximum order of image source reflections drawn on screen",
            default=3,
            )

    enable_auralization: BoolProperty(
            name="Enable auralization",
            description='Activate real-time update of the Evertims client from Blender 3D view',
            default=False,
            )
    debug_logs: BoolProperty(
            name="Print Logs",
            description='Print logs of the EVERTims python module in Blender console',
            default=False,
            )

    # Scene components
    room_group: StringProperty(
            name="Room",
            description="Current room selected for auralization",
            default="", maxlen=1024,
            )
    listener_object: StringProperty(
            name="Listener",
            description="Current listener selected for auralization",
            default="", maxlen=1024,
            )
    source_object: StringProperty(
            name="Source",
            description="Current source selected for auralization",
            default="", maxlen=1024,
            )
    materials: StringProperty(
            name="Material",
            description="A string (shaped from dict) of all available materials and their properties",
            default="", maxlen=0, # unlimited length
            )
    export_file_path: StringProperty(
            name="Export scene file path",
            description="Path to which scene will be exported",
            default="//evert-export.txt", maxlen=1024, subtype="FILE_PATH",
            )

    # Source directivity
    source_directivity_type: EnumProperty(
            name="Directivity type",
            description="Method used to define source directivity",
            items={
            # ("file", "File", "Loaded SOFA file"),
            ("disabled", "Disabled", "Source is omni-directional"),
            ("custom", "Custom", "Custom procedural directivity"),
            },
            default="disabled")
    source_directivity_frequencies: IntVectorProperty(
            name="Directivity frequencies",
            description="Center frequency bands of source directivity coefficients",
            size=8,
            default= (125, 250, 500, 1000, 2000, 4000, 8000, 16000),
            subtype = "NONE"
            )
    source_directivity_values: FloatVectorProperty(
            name="Directivity values",
            description="Source directivity coefficients, in 0-100, 0 is omni-directional",
            size=8,
            default=(0, 10, 20, 30, 40, 50, 60, 70),
            min = 0,
            max = 100,
            soft_min=0,
            soft_max=100,
            precision = 1,
            subtype = "NONE"
            )


class EvertimsPreferences(AddonPreferences):
    # bl_idname = __name__
    bl_idname = __package__

    material_file_path: StringProperty(
            name="Path to material definition file",
            description="Path to the file that hold acoustic materials definition",
            default="//", maxlen=1024, subtype="FILE_PATH",
            )


# ############################################################
# Register / Unregister
# ############################################################


def register():

    bpy.utils.register_class(EvertimsSettings)
    bpy.utils.register_class(EvertimsPreferences)

    operators.register()
    ui.register()

    bpy.types.Scene.evertims = PointerProperty(type=EvertimsSettings)


def unregister():

    bpy.utils.unregister_class(EvertimsSettings)
    bpy.utils.unregister_class(EvertimsPreferences)

    ui.unregister()
    operators.unregister()

    del bpy.types.Scene.evertims
