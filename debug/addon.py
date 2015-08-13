if "bpy" in locals():
    import imp
    imp.reload(engine)
else:
    import bpy
    from .brte import engine

class DebugEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'RTE_DEBUG'
    bl_label = 'RTE Debug'
