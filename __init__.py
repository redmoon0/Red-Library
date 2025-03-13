bl_info = {
	"name": "Red Library",
	"description": "Red Assets Library",
	"author": "Redmoon",
	"version": (1, 0, 0),
	"blender": (4, 0, 0),
	"location": "View 3D > Tool Shelf > Demo Updater",
	"warning": "",
	"wiki_url": "https://github.com/redmoon0/Red-Library",
	"tracker_url": "https://github.com/redmoon0/Red-Library/issues",
	"category": "System"
}


import bpy
import os
from . import addon_updater_ops

# Cache for loaded materials
materials_cache = []

# Load materials from the specified external blend file
def load_materials_from_external_blend():
    global materials_cache
    if materials_cache:
        return materials_cache

    prefs = bpy.context.preferences.addons[__name__].preferences
    external_blender_file = prefs.external_blender_file

    if not os.path.exists(external_blender_file):
        print("Invalid file path.")
        return []

    with bpy.data.libraries.load(external_blender_file, link=True) as (data_from, data_to):
        data_to.materials = data_from.materials

    materials_cache = data_to.materials
    return materials_cache

class RedLibraryPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    auto_check_update: bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False
    )

    updater_interval_months: bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_interval_days: bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=0,
        min=0
    )
    updater_interval_hours: bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0
    )
    updater_interval_minutes: bpy.props.IntProperty(
        name='minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0
    )

    external_blender_file: bpy.props.StringProperty(
        name="External Blender File",
        description="Path to the Blender file containing materials",
        default="",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout
        addon_updater_ops.update_settings_ui(self, context)
        layout.prop(self, "external_blender_file", text="Path to Blender File")

class ApplyMaterialOperator(bpy.types.Operator):
    bl_idname = "object.apply_material"
    bl_label = "Apply Material"
    material_name: bpy.props.StringProperty()

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        if active_obj and active_obj.type == 'MESH':
            material = bpy.data.materials.get(self.material_name)
            if material:
                if len(active_obj.data.materials) == 0:
                    active_obj.data.materials.append(material)
                else:
                    active_obj.data.materials[0] = material
                self.report({'INFO'}, f"Material '{material.name}' applied for preview.")
            else:
                self.report({'ERROR'}, f"Material '{self.material_name}' not found.")
        else:
            self.report({'ERROR'}, "No active mesh object.")
        return {'FINISHED'}

class ImportAndApplyMaterialOperator(bpy.types.Operator):
    bl_idname = "object.import_and_apply_material"
    bl_label = "Import and Apply Material"
    material_name: bpy.props.StringProperty()

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        if not active_obj or active_obj.type != 'MESH':
            self.report({'ERROR'}, "No active mesh object.")
            return {'CANCELLED'}

        prefs = bpy.context.preferences.addons[__name__].preferences
        external_blender_file = prefs.external_blender_file

        if not os.path.exists(external_blender_file):
            self.report({'ERROR'}, "External Blender file not found.")
            return {'CANCELLED'}

        with bpy.data.libraries.load(external_blender_file, link=False) as (data_from, data_to):
            if self.material_name not in data_from.materials:
                self.report({'ERROR'}, f"Material '{self.material_name}' not found in external file.")
                return {'CANCELLED'}
            data_to.materials = [self.material_name]

        if not data_to.materials:
            self.report({'ERROR'}, "Failed to import material.")
            return {'CANCELLED'}

        material = data_to.materials[0]
        if len(active_obj.data.materials) == 0:
            active_obj.data.materials.append(material)
        else:
            active_obj.data.materials[0] = material

        self.report({'INFO'}, f"Imported and applied '{material.name}'.")
        return {'FINISHED'}

class MaterialPreviewPanel(bpy.types.Panel):
    bl_label = "Red Library"
    bl_idname = "MATERIALS_PT_preview"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Red Library'

    def draw(self, context):
        layout = self.layout
        materials = load_materials_from_external_blend()

        for material in materials:
            box = layout.row()
            box.label(text=material.name)
            preview_box = layout.box()
            if material.preview:
                preview_box.template_icon(icon_value=material.preview.icon_id, scale=5)
            else:
                preview_box.label(text="No Preview Available")
            row = preview_box.row()
            row.operator("object.apply_material", text="Preview").material_name = material.name
            row.operator("object.import_and_apply_material", text="Apply").material_name = material.name

class DemoUpdaterPanel(bpy.types.Panel):
    bl_label = "Red Library Updater"
    bl_idname = "DEMO_UPDATER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Red Library 2'

    def draw(self, context):
        layout = self.layout
        addon_updater_ops.check_for_update_background()
        if addon_updater_ops.updater.update_ready:
            layout.label(text="Custom update message", icon="INFO")
        addon_updater_ops.update_notice_box_ui(self, context)

classes = (
    RedLibraryPreferences,
    DemoUpdaterPanel,
    ApplyMaterialOperator,
    ImportAndApplyMaterialOperator,
    MaterialPreviewPanel
)

def register():
    addon_updater_ops.register(bl_info)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    addon_updater_ops.unregister()
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f"Error unregistering {cls}: {e}")