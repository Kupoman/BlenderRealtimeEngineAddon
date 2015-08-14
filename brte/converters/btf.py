from . import blendergltf


class BTFConverter:
    def convert(self, add_delta, update_delta, remove_delta, callback):
        add_delta.update(update_delta)
        data = blendergltf.export_gltf(add_delta)
        if callback:
            callback(data)
