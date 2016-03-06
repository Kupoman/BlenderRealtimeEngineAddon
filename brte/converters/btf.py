if 'imported' in locals():
    import imp
    import bpy
    imp.reload(blendergltf)
else:
    imported = True
    from . import blendergltf


import json
import math

import bpy


def togl(matrix):
    return [i for col in matrix.col for i in col]


class BTFConverter:
    def convert(self, add_delta, update_delta, remove_delta, view_delta):
        for key, value in update_delta.items():
            if value:
                add_delta[key] = value

        data = blendergltf.export_gltf(add_delta)

        self.export_view(view_delta, data)

        return data

    def export_view(self, view_delta, gltf):
        if 'extras' not in gltf:
            gltf['extras'] = {}

        if 'viewport' in view_delta:
            gltf['extras']['view'] = {
                'width' : view_delta['viewport'].width,
                'height' : view_delta['viewport'].width,
                'projection_matrix': togl(view_delta['projection_matrix']),
                'view_matrix': togl(view_delta['view_matrix']),
            }
