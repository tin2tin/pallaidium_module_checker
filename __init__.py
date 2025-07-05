# Location: a panel in the Text Editor's sidebar.

bl_info = {
    "name": "Pallaidium Module Checker",
    "author": "tintwotin",
    "version": (2, 6, 0),
    "blender": (3, 0, 0),
    "location": "Text Editor > Sidebar > Pallaidium Test",
    "description": "Scans and tests all available models in the 'Pallaidium - Generative AI' add-on.",
    "category": "Testing",
    "doc_url": "https://github.com/tin2tin/Pallaidium",
}

import bpy
import traceback

# --- Configuration & Helpers ---

PALLAIDIUM_MODULE_NAME = "bl_ext.user_default.pallaidium_generative_ai"
PALLAIDIUM_OPERATOR_IDNAME = "SEQUENCER_OT_generate_image" 

def is_pallaidium_enabled():
    """Checks if Pallaidium is enabled by looking for one of its core operators."""
    return hasattr(bpy.types, PALLAIDIUM_OPERATOR_IDNAME)


# --- Properties ---
class PallaidiumTestModel(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Model Name")
    is_tested: bpy.props.BoolProperty(name="Test This Model", default=True)
    model_type: bpy.props.StringProperty(name="Model Type")
    model_id: bpy.props.StringProperty(name="Model Identifier")

class PallaidiumTestSettings(bpy.types.PropertyGroup):
    models: bpy.props.CollectionProperty(type=PallaidiumTestModel)
    is_initialized: bpy.props.BoolProperty(name="Has Scanned for Models", default=False)


# --- Operators ---

class PALLAIDIUM_OT_ToggleAll(bpy.types.Operator):
    """Enable or disable all models at once."""
    bl_idname = "pallaidium.toggle_all"
    bl_label = "Toggle All Models"
    
    mode: bpy.props.EnumProperty(items=[('ON', 'On', 'Enable all'), ('OFF', 'Off', 'Disable all')])
    
    def execute(self, context):
        settings = context.scene.pallaidium_test_settings
        new_state = (self.mode == 'ON')
        for model in settings.models:
            model.is_tested = new_state
        return {'FINISHED'}

class PALLAIDIUM_OT_ToggleType(bpy.types.Operator):
    """Enable or disable all models of a specific type."""
    bl_idname = "pallaidium.toggle_type"
    bl_label = "Toggle Model Type"
    
    mode: bpy.props.EnumProperty(items=[('ON', 'On', 'Enable type'), ('OFF', 'Off', 'Disable type')])
    model_type: bpy.props.StringProperty()
    
    def execute(self, context):
        settings = context.scene.pallaidium_test_settings
        new_state = (self.mode == 'ON')
        for model in settings.models:
            if model.model_type == self.model_type:
                model.is_tested = new_state
        return {'FINISHED'}

class PALLAIDIUM_OT_RefreshModels(bpy.types.Operator):
    """Scans the Pallaidium addon's preferences to find all available models."""
    bl_idname = "pallaidium.refresh_models"
    bl_label = "Scan for Pallaidium Models"

    def execute(self, context):
        settings = context.scene.pallaidium_test_settings
        settings.models.clear()
        
        if PALLAIDIUM_MODULE_NAME not in bpy.context.preferences.addons:
            self.report({'ERROR'}, f"Could not find Add-on: {PALLAIDIUM_MODULE_NAME}")
            return {'CANCELLED'}
        prefs = bpy.context.preferences.addons[PALLAIDIUM_MODULE_NAME].preferences
        model_props_to_scan = {
            'image_model_card': 'IMAGE', 'text_model_card': 'TEXT',
            'audio_model_card': 'AUDIO', 'movie_model_card': 'MOVIE',
        }
        try:
            total_models_found = 0
            for prop_name, model_type in model_props_to_scan.items():
                prop_info = prefs.rna_type.properties.get(prop_name)
                if prop_info and hasattr(prop_info, 'enum_items'):
                    for enum_item in prop_info.enum_items:
                        item = settings.models.add()
                        item.name = enum_item.name
                        item.model_type = model_type
                        item.model_id = enum_item.identifier
                        total_models_found += 1
        except Exception as e:
            self.report({'ERROR'}, f"Error during scan. See System Console.")
            traceback.print_exc()
            settings.is_initialized = False
            return {'CANCELLED'}
        settings.is_initialized = True
        self.report({'INFO'}, f"Scan complete. Found {total_models_found} models.")
        return {'FINISHED'}

class PALLAIDIUM_OT_RunTests(bpy.types.Operator):
    """Runs inference tests on the selected Pallaidium models."""
    bl_idname = "pallaidium.run_tests"
    bl_label = "Run Selected Tests"

    @classmethod
    def poll(cls, context):
        settings = context.scene.pallaidium_test_settings
        return settings.is_initialized and len(settings.models) > 0

    def execute(self, context):
        if PALLAIDIUM_MODULE_NAME not in bpy.context.preferences.addons:
            self.report({'ERROR'}, f"Could not find Add-on: {PALLAIDIUM_MODULE_NAME}")
            return {'CANCELLED'}
        settings = context.scene.pallaidium_test_settings
        prefs = bpy.context.preferences.addons[PALLAIDIUM_MODULE_NAME].preferences
        
        # Start the Markdown report with a header
        report_lines = [
            "| Model | Status | Notes |",
            "|---|---|---|"
        ]
        
        models_to_test = [m for m in settings.models if m.is_tested]
        if not models_to_test:
            self.report({'WARNING'}, "No models were selected for testing.")
            return {'CANCELLED'}

        for model in models_to_test:
            self.report({'INFO'}, f"Testing: {model.name}...")
            try:
                if model.model_type == 'IMAGE':
                    prefs.image_model_card = model.model_id
                    bpy.ops.sequencer.generate_image()
                elif model.model_type == 'TEXT':
                    prefs.text_model_card = model.model_id
                    bpy.ops.sequencer.generate_text()
                elif model.model_type == 'AUDIO':
                    prefs.audio_model_card = model.model_id
                    bpy.ops.sequencer.generate_audio()
                elif model.model_type == 'MOVIE':
                    prefs.movie_model_card = model.model_id
                    bpy.ops.sequencer.generate_movie()
                
                # Add a success row to the Markdown table
                report_lines.append(f"| {model.name} | ✅ | Works as expected. |")

            except Exception as e:
                # Sanitize the error message to not break the table
                error_message = str(e).replace("\n", " ").strip().replace("|", "\|")
                # Add a failure row to the Markdown table
                report_lines.append(f"| {model.name} | ❌ | Error: {error_message} |")
        
        # Create a new text block with a .md extension
        report_text = bpy.data.texts.new("Pallaidium Test Report.md")
        report_text.write("\n".join(report_lines))
        
        self.report({'INFO'}, "All tests complete. Report created in Text Editor.")
        return {'FINISHED'}

# --- UI Panel ---
class PALLAIDIUM_PT_TestPanel(bpy.types.Panel):
    bl_label = "Pallaidium Test Kit"
    bl_idname = "TEXT_PT_pallaidium_test"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Pallaidium Test'

    def draw(self, context):
        layout = self.layout
        if not is_pallaidium_enabled():
            layout.box().label(text="Pallaidium add-on is not enabled.", icon='ERROR')
            return

        settings = context.scene.pallaidium_test_settings
        layout.operator("pallaidium.refresh_models", icon='FILE_REFRESH')
        
        if settings.is_initialized:
            if not settings.models:
                layout.label(text="No models found. Press Scan again.", icon='INFO')
                return

            row = layout.row(align=True)
            all_enabled = all(m.is_tested for m in settings.models)
            if all_enabled:
                op = row.operator("pallaidium.toggle_all", text="Disable All", icon='CHECKBOX_HLT')
                op.mode = 'OFF'
            else:
                op = row.operator("pallaidium.toggle_all", text="Enable All", icon='CHECKBOX_DEHLT')
                op.mode = 'ON'

            model_types = sorted(list(set(m.model_type for m in settings.models)))
            for model_type in model_types:
                box = layout.box()
                header = box.row(align=True)
                type_models = [m for m in settings.models if m.model_type == model_type]
                type_all_enabled = all(m.is_tested for m in type_models)

                header.label(text=f"{model_type.title()} Models", icon='MOD_WAVE')

                if type_all_enabled:
                    op = header.operator("pallaidium.toggle_type", text="", icon='CHECKBOX_HLT')
                    op.mode = 'OFF'
                    op.model_type = model_type
                else:
                    op = header.operator("pallaidium.toggle_type", text="", icon='CHECKBOX_DEHLT')
                    op.mode = 'ON'
                    op.model_type = model_type

                for model in type_models:
                    box.prop(model, "is_tested", text=model.name)
            
            layout.separator()
            layout.operator("pallaidium.run_tests", icon='PLAY')
        else:
            layout.label(text="Click 'Scan' to find available models.", icon='INFO')

# --- Registration ---
classes = (
    PallaidiumTestModel,
    PallaidiumTestSettings,
    PALLAIDIUM_OT_ToggleAll,
    PALLAIDIUM_OT_ToggleType,
    PALLAIDIUM_OT_RefreshModels,
    PALLAIDIUM_OT_RunTests,
    PALLAIDIUM_PT_TestPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.pallaidium_test_settings = bpy.props.PointerProperty(type=PallaidiumTestSettings)

def unregister():
    if hasattr(bpy.types.Scene, 'pallaidium_test_settings'):
        del bpy.types.Scene.pallaidium_test_settings
    for cls in reversed(classes):
        if hasattr(bpy.utils, "unregister_class"):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass

if __name__ == "__main__":
    register()
