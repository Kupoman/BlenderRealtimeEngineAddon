if "bpy" in locals():
    import imp
    # imp.reload(renderer)
    # imp.reload(converter)
else:
    import bpy


def get_collection_name(collection):
    class_name = collection.rna_type.__class__.__name__
    clean_name = class_name.replace("BlendData", "").lower()
    return clean_name

class RealTimeEngine(bpy.types.RenderEngine):
    bl_idname = 'RTE_FRAMEWORK'
    bl_label = "Real Time Engine Framework"

    def __init__(self):
        self._watch_list = [
            bpy.data.actions,
            bpy.data.armatures,
            bpy.data.cameras,
            bpy.data.curves,
            bpy.data.groups,
            bpy.data.images,
            bpy.data.lattices,
            bpy.data.libraries,
            bpy.data.lamps,
            bpy.data.materials,
            bpy.data.meshes,
            bpy.data.metaballs,
            bpy.data.movieclips,
            bpy.data.node_groups,
            bpy.data.objects,
            bpy.data.particles,
            bpy.data.scenes,
            # bpy.data.shape_keys,
            bpy.data.sounds,
            bpy.data.speakers,
            bpy.data.texts,
            bpy.data.textures,
            bpy.data.worlds,
        ]

        self._tracking_sets = {}
        for collection in self._watch_list:
            collection_name = get_collection_name(collection)
            self._tracking_sets[collection_name] = set()

    def view_update(self, context):
        """ Called when the scene is changed """
        for collection in self._watch_list:
            collection_name = get_collection_name(collection)
            collection_set = set(collection)
            tracking_set = self._tracking_sets[collection_name]

            # Check for new items
            add_method = getattr(self, "add_"+collection_name, self.add_data)
            add_set = collection_set - tracking_set
            add_method(add_set)
            tracking_set |= add_set

            # Check for removed items
            remove_method = getattr(self, "remove_"+collection_name, self.remove_data)
            remove_set = tracking_set - collection_set
            remove_method(remove_set)
            tracking_set -= remove_set

            # Check for updates
            update_method = getattr(self, "update_"+collection_name, self.update_data)
            update_set = [item for item in collection if item.is_updated]
            update_method(update_set)

    def view_draw(self, context):
        """ Called when viewport settings change """
        region = context.region
        view = context.region_data

        vmat = view.view_matrix.copy()
        vmat_inv = vmat.inverted()
        pmat = view.perspective_matrix * vmat_inv

        viewport = [region.x, region.y, region.width, region.height]

        self.update_view(vmat, pmat, viewport)

    def add_objects(self, add_set):
        for data in add_set:
            print(data.__class__.__name__, data.name, "added with Object add")

    def remove_objects(self, add_set):
        for data in add_set:
            print(data.__class__.__name__, data.name, "removed with Object remove")

    def update_objects(self, add_set):
        for data in add_set:
            print(data.__class__.__name__, data.name, "updated with Object update")

    def add_data(self, add_set):
        for data in add_set:
            print(data.__class__.__name__, data.name, "added with generic add")

    def remove_data(self, remove_set):
        for data in remove_set:
            print(data.__class__.__name__, data.name, "removed with generic remove")

    def update_data(self, update_set):
        for data in update_set:
            print(data.__class__.__name__, data.name, "updated with generic update")

    def update_view(self, view_matrix, projection_matrix, viewport):
        print(view_matrix)
        print(projection_matrix)
        print(viewport)


