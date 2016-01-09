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
        gltf['extras']['view'] = {'camera_node' : 'view_camera_node'}

        if 'viewport' in view_delta:
            gltf['extras']['view']['width'] = view_delta['viewport'].width
            gltf['extras']['view']['height'] = view_delta['viewport'].height

        if 'view_matrix' in view_delta:
            # Update node
            if 'nodes' not in gltf:
                gltf['nodes'] = {}
            gltf['nodes']['view_camera_node'] = {
                'camera' : 'view_camera',
                'matrix' : blendergltf.togl(view_delta['view_matrix'])
            }

        if 'projection_matrix' in view_delta:
            space = [a.spaces[0] for a in bpy.context.screen.areas if a.type == 'VIEW_3D'][0]
            region = space.region_3d
            if 'cameras' not in gltf:
                gltf['cameras'] = {}

            if region.is_perspective:
                aspect = view_delta['projection_matrix'][1][1] / view_delta['projection_matrix'][0][0]
                yfov = math.radians(space.lens) / aspect
                gltf['cameras']['view_camera'] = {
                    'type' : 'perspective',
                    'perspective' : {
                        'aspectRatio' : aspect,
                        'yfov' : yfov,
                        'zfar' : space.clip_end,
                        'znear' : space.clip_start,
                    }
                }
            else:
                scale_x = 2 / view_delta['projection_matrix'][0][0]
                scale_y = 2 / view_delta['projection_matrix'][1][1]
                gltf['cameras']['view_camera'] = {
                    'type' : 'orthographic',
                    'orthographic' : {
                        'xmag' : scale_x,
                        'ymag' : scale_y,
                        'zfar' : space.clip_end,
                        'znear' : space.clip_start,
                    }
                }
