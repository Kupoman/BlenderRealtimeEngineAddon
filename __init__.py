bl_info = {
    "name": "Real Time Engine Framework",
    "author": "Daniel Stokes",
    "blender": (2, 70, 0),
    "location": "Info header, render engine menu",
    "description": "Framework for integrating real time engines",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'TESTING',
    "category": "Render"}


if "bpy" in locals():
    import imp
    unregister()
    imp.reload(engine)
else:
    import bpy
    from . import engine

import bl_ui

def register():
    panels = [getattr(bpy.types, t) for t in dir(bpy.types) if 'PT' in t]
    for panel in panels:
        if hasattr(panel, 'COMPAT_ENGINES') and 'BLENDER_GAME' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.add('RTE_FRAMEWORK')

    bpy.utils.register_module(__name__)


def unregister():
    panels = [getattr(bpy.types, t) for t in dir(bpy.types) if 'PT' in t]
    for panel in panels:
        if hasattr(panel, 'COMPAT_ENGINES') and 'RTE_FRAMEWORK' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('RTE_FRAMEWORK')

    bpy.utils.unregister_module(__name__)
