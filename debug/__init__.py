bl_info = {
    "name": "RTE Debug",
    "author": "Daniel Stokes",
    "blender": (2, 75, 0),
    "location": "Info header, render engine menu",
    "description": "Debug implementation of the Realtime Engine Framework",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'TESTING',
    "category": "Render"}

import bpy

import sys
from .addon import DebugEngine


def register():
    panels = [getattr(bpy.types, t) for t in dir(bpy.types) if 'PT' in t]
    for panel in panels:
        if hasattr(panel, 'COMPAT_ENGINES') and 'BLENDER_GAME' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.add('RTE_DEBUG')
    bpy.utils.register_module(__name__)


def unregister():
    panels = [getattr(bpy.types, t) for t in dir(bpy.types) if 'PT' in t]
    for panel in panels:
        if hasattr(panel, 'COMPAT_ENGINES') and 'RTE_FRAMEWORK' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('RTE_DEBUG')
    bpy.utils.unregister_module(__name__)
