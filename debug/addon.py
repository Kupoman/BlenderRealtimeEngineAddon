import bpy

from .brte.engine import RealTimeEngine


class DebugEngine(bpy.types.RenderEngine, RealTimeEngine):
    bl_idname = 'RTE_DEBUG'
    bl_label = 'RTE Debug'
