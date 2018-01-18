if 'imported' in locals():
    import imp
    import bpy
    imp.reload(blendergltf)
else:
    imported = True
    import blendergltf


import json
import math

import bpy


def togl(matrix):
    return [i for col in matrix.col for i in col]


class BTFConverter:
    def __init__(self, gltf_settings=None):
        if gltf_settings is None:
            available_extensions = blendergltf.extension_exporters
            gltf_settings = {
                'images_data_storage': 'REFERENCE',
                'nodes_export_hidden': True,
                'images_allow_srgb': True,
                'asset_profile': 'DESKTOP',
                'asset_version': '1.0',
                'hacks_streaming': True,
                'meshes_apply_modifiers': False, # Cannot be done in a thread
                'extension_exporters': [
                    available_extensions.khr_materials_common.KhrMaterialsCommon(),
                    available_extensions.blender_physics.BlenderPhysics(),
                ],
            }

        self.gltf_settings = gltf_settings

    def convert(self, add_delta, update_delta, remove_delta, view_delta):
        for key, value in update_delta.items():
            if value:
                add_delta[key] = value

        data = blendergltf.export_gltf(add_delta, self.gltf_settings)

        if view_delta:
            self.export_view(view_delta, data)

        return data

    def export_view(self, view_delta, gltf):
        if 'extras' not in gltf:
            gltf['extras'] = {}
        gltf['extras']['view'] = {}

        if 'viewport' in view_delta:
            gltf['extras']['view'] = {
                'width' : view_delta['viewport'].width,
                'height' : view_delta['viewport'].height,
            }
        if 'projection_matrix' in view_delta:
            gltf['extras']['view']['projection_matrix'] = togl(view_delta['projection_matrix'])
        if 'view_matrix' in view_delta:
            gltf['extras']['view']['view_matrix'] = togl(view_delta['view_matrix'])
