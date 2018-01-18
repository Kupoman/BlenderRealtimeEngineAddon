if "bpy" in locals():
    import imp
    imp.reload(socket_api)
    imp.reload(_converters)
    imp.reload(processors)
    imp.reload(converter_thread)
    imp.reload(processor_thread)
else:
    import bpy
    from . import socket_api
    from . import converters as _converters
    from . import processors
    from . import converter_thread
    from . import processor_thread

import os
import socket
import struct
import subprocess
import sys
import time
import threading
import collections
import queue

import bpy
import mathutils

from OpenGL.GL import *


DEFAULT_WATCHLIST = [
    #"actions",
    #"armatures",
    "cameras",
    "images",
    "lamps",
    "materials",
    "meshes",
    "objects",
    "scenes",
    #"sounds",
    #"speakers",
    "textures",
    #"worlds",
]


ViewportTuple = collections.namedtuple('Viewport', ('height', 'width'))


# Currently need some things stored globally so they can be cleaned up after
# losing the RealTimeEngine reference
class G:
    done_event = None
    thread_converter = None
    thread_processor = None

    def cleanup_threads():
        if threading.get_ident() != threading.main_thread().ident:
            # Only let the main thread cleanup threads
            return

        if G.done_event is not None:
            G.done_event.set()
        if G.thread_converter is not None:
            G.thread_converter.join()
            G.thread_converter = None
        if G.thread_processor is not None:
            G.thread_processor.join()
            G.thread_processor = None


def get_collection_name(collection):
    class_name = collection.rna_type.__class__.__name__
    clean_name = class_name.replace("BlendData", "").lower()
    return clean_name


class RealTimeEngine():
    bl_idname = 'RTE_FRAMEWORK'
    bl_label = "Real Time Engine Framework"

    def __init__(self, **kwargs):
        # Display image
        self.clock = time.perf_counter()

        self.queue_pre_convert = queue.Queue()
        self.queue_post_convert = queue.Queue()
        self.queue_update = queue.Queue()
        self.queue_image = queue.Queue()

        G.cleanup_threads()

        G.done_event = threading.Event()

        converter = kwargs.get('converter', _converters.BTFConverter())
        G.thread_converter = converter_thread.ConverterThread(converter,
            self.queue_pre_convert, self.queue_post_convert, G.done_event)
        G.thread_converter.start()

        processor = kwargs.get('processor', processors.DummyProcessor())
        G.thread_processor = processor_thread.ProcessorThread(processor,
            self.queue_post_convert, self.queue_update, self.queue_image,
            G.done_event)
        G.thread_processor.start()

        self.use_bgr_texture = kwargs.get('use_bgr_texture', False)

        self.remove_delta = {}
        self.add_delta = {}
        self.update_delta = {}
        self.view_delta = {}

        watch_list = kwargs['watch_list'] if 'watch_list' in kwargs else DEFAULT_WATCHLIST
        self._watch_list = [getattr(bpy.data, i) for i in watch_list]

        self._tracking_sets = {}
        for collection in self._watch_list:
            collection_name = get_collection_name(collection)
            self._tracking_sets[collection_name] = set()

        self._old_vmat = None
        self._old_pmat = None
        self._old_viewport = None

        def main_loop(scene):
            if threading.get_ident() != threading.main_thread().ident:
                print("Wrong thread", threading.current_thread())
                import inspect
                for i in inspect.stack():
                    print(str(i))
                return

            try:
                new_time = time.perf_counter()
                dt = new_time - self.clock
                self.clock = new_time
                self.main_update(dt)
            except ReferenceError:
                bpy.app.handlers.scene_update_post.remove(main_loop)
                G.cleanup_threads()

        bpy.app.handlers.scene_update_post.append(main_loop)

        self.tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0,
            GL_RGB, GL_UNSIGNED_BYTE, struct.pack('=BBB', 0, 0, 0))

    def __del__(self):
        G.cleanup_threads()

    @classmethod
    def register(cls):
        render_engine_class = cls
        class LaunchGame(bpy.types.Operator):
            '''Launch the game in a separate window'''
            bl_idname = '{}.launch_game'.format(cls.bl_idname.lower())
            bl_label = 'Launch Game'

            @classmethod
            def poll(cls, context):
                return context.scene.render.engine == render_engine_class.bl_idname

            def execute(self, context):
                try:
                    cls.launch_game()
                except:
                    self.report({'ERROR'}, str(sys.exc_info()[1]))
                return {'FINISHED'}

        bpy.utils.register_class(LaunchGame)
        if not bpy.app.background:
            km = bpy.context.window_manager.keyconfigs.default.keymaps['Screen']
            ki = km.keymap_items.new(LaunchGame.bl_idname, 'P', 'PRESS')

    def view_update(self, context):
        """ Called when the scene is changed """

        for collection in self._watch_list:
            collection_name = get_collection_name(collection)
            collection_set = set(collection)
            tracking_set = self._tracking_sets[collection_name]

            # Check for new items
            add_set = collection_set - tracking_set
            self.add_delta[collection_name] = add_set
            tracking_set |= add_set

            # Check for removed items
            remove_set = tracking_set - collection_set
            self.remove_delta[collection_name] = remove_set
            tracking_set -= remove_set

            # Check for updates
            update_set = {item for item in collection if item.is_updated}
            self.update_delta[collection_name] = update_set

    def view_draw(self, context):
        """ Called when viewport settings change """
        region = context.region
        view = context.region_data

        vmat = view.view_matrix.copy()
        vmat_inv = vmat.inverted()
        pmat = view.perspective_matrix * vmat_inv

        viewport = [region.x, region.y, region.width, region.height]

        self.update_view(vmat, pmat, viewport)


        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        try:
            image_ref = self.queue_image.get_nowait()
            image_format = GL_BGR if self.use_bgr_texture else GL_RGB
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, image_ref[0], image_ref[1], 0, image_format,
                GL_UNSIGNED_BYTE, image_ref[2])
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            self.queue_image.task_done()
        except queue.Empty:
            pass

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_STENCIL_TEST)
        glEnable(GL_TEXTURE_2D)

        glClearColor(0, 0, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        glBegin(GL_QUADS)
        glColor3f(1.0, 1.0, 1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3i(-1, -1, 0)
        glTexCoord2f(1.0, 0.0)
        glVertex3i(1, -1, 0)
        glTexCoord2f(1.0, 1.0)
        glVertex3i(1, 1, 0)
        glTexCoord2f(0.0, 1.0)
        glVertex3i(-1, 1, 0)
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glPopAttrib()

    def update_view(self, view_matrix, projection_matrix, viewport):
        if view_matrix != self._old_vmat:
            self._old_vmat = view_matrix
            self.view_delta['view_matrix'] = view_matrix

        if projection_matrix != self._old_pmat:
            self._old_pmat = projection_matrix
            self.view_delta['projection_matrix'] = projection_matrix

        if viewport != self._old_viewport:
            self._old_viewport = viewport
            self.view_delta['viewport'] = ViewportTuple(width=viewport[2], height=viewport[3])

    def draw_callback(self):
        '''Forces a view_draw to occur'''
        self.tag_redraw()

    def main_update(self, dt):
        if self.add_delta or self.update_delta or self.view_delta:
            self.queue_pre_convert.put((
                self.add_delta.copy(),
                self.update_delta.copy(),
                self.remove_delta.copy(),
                self.view_delta.copy(),
            ))

        self.add_delta.clear()
        self.update_delta.clear()
        self.remove_delta.clear()
        self.view_delta.clear()

        self.queue_update.put(dt)

        self.draw_callback()

        # Useful debug information for checking if a queue is filling up
        # print('Approximate queue sizes:')
        # print('\tPre Convert:', self.queue_pre_convert.qsize())
        # print('\tPost Convert:', self.queue_post_convert.qsize())
        # print('\tUpdate:', self.queue_update.qsize())
        # print('\tImage:', self.queue_image.qsize())

    @classmethod
    def launch_game(cls):
        pass
