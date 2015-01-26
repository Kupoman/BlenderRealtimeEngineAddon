if "bpy" in locals():
    import imp
    # imp.reload(renderer)
    # imp.reload(converter)
else:
    import bpy

from bgl import *

DEFAULT_WATCHLIST = [
    "actions",
    "armatures",
    "cameras",
    "images",
    "lamps",
    "materials",
    "meshes",
    "objects",
    "scenes",
    "sounds",
    "speakers",
    "textures",
    "worlds",
]


def get_collection_name(collection):
    class_name = collection.rna_type.__class__.__name__
    clean_name = class_name.replace("BlendData", "").lower()
    return clean_name

class RealTimeEngine(bpy.types.RenderEngine):
    bl_idname = 'RTE_FRAMEWORK'
    bl_label = "Real Time Engine Framework"

    def __init__(self, watch_list=DEFAULT_WATCHLIST):
        self._watch_list = [getattr(bpy.data, i) for i in watch_list]

        self._tracking_sets = {}
        for collection in self._watch_list:
            collection_name = get_collection_name(collection)
            self._tracking_sets[collection_name] = set()

        # Display image
        self.width = 1
        self.height = 1
        self.display = Buffer(GL_BYTE, 3, [0, 0, 0])

        self._old_vmat = None
        self._old_pmat = None
        self._old_viewport = None

        def main_loop(scene):
            try:
                self.scene_callback()
            except ReferenceError:
                bpy.app.handlers.scene_update_post.remove(main_loop)

        bpy.app.handlers.scene_update_post.append(main_loop)

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

        glGetError()
        glPushAttrib(GL_ALL_ATTRIB_BITS)

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_TEXTURE_2D)

        glClearColor(0, 0, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        bgl_buffer = Buffer(GL_INT, 1)
        glActiveTexture(GL_TEXTURE0)
        glGenTextures(1, bgl_buffer)
        tex = bgl_buffer[0]
        glBindTexture(GL_TEXTURE_2D, tex)
        width = viewport[2] - viewport[0]
        height = viewport[3] - viewport[1]
        glTexImage2D(GL_TEXTURE_2D, 0, 3, self.width, self.height, 0, GL_RGB, GL_BYTE, self.display)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3i(-1, -1, 0)
        glTexCoord2f(1.0, 0.0)
        glVertex3i(1, -1, 0)
        glTexCoord2f(1.0, 1.0)
        glVertex3i(1, 1, 0)
        glTexCoord2f(0.0, 1.0)
        glVertex3i(-1, 1, 0)
        glEnd()

        glDeleteTextures(1, bgl_buffer)

        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glPopAttrib()

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
        print("update_view")
        if view_matrix != self._old_vmat:
            print(view_matrix)
        if projection_matrix != self._old_pmat:
            print(projection_matrix)
        if viewport != viewport:
            print(viewport)

    def scene_callback(self):
        pass

