if 'imported' in locals():
    import imp
    imp.reload(blendergltf)
else:
    imported = True
    from . import blendergltf


import json


class BTFConverter:
    def convert(self, add_delta, update_delta, remove_delta, view_delta, callback):
        for key, value in update_delta.items():
            if value:
                add_delta[key] = value

        data = blendergltf.export_gltf(add_delta)

        if callback:
            callback(data)
