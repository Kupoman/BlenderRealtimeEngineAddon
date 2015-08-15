if "bpy" in locals():
    import imp
    imp.reload(socket_api)
    imp.reload(_converters)
    imp.reload(processors)
else:
    import bpy
    from . import socket_api
    from . import converters as _converters
    from . import processors

import os
import socket
import struct
import subprocess
import sys
import time

import bpy
import mathutils

from OpenGL.GL import *


DEFAULT_WATCHLIST = [
    #"actions",
    #"armatures",
    "cameras",
    #"images",
    "lamps",
    "materials",
    "meshes",
    "objects",
    "scenes",
    #"sounds",
    #"speakers",
    #"textures",
    #"worlds",
]


class _BaseFunc:
    def __call__(self, data_set):
        pass


def get_collection_name(collection):
    class_name = collection.rna_type.__class__.__name__
    clean_name = class_name.replace("BlendData", "").lower()
    return clean_name


class RealTimeEngine():
    bl_idname = 'RTE_FRAMEWORK'
    bl_label = "Real Time Engine Framework"

    def __init__(self, program=[], watch_list=DEFAULT_WATCHLIST):
        # Display image
        self.width = 1
        self.height = 1
        self.clock = time.perf_counter()
        self.display = processors.DoubleBuffer(3, self.draw_callback)

        self.draw_lock = False
        self.override_context = None

        self.converter = _converters.BTFConverter()
        self.processor = processors.DummyProcessor(self.display)

        self._watch_list = [getattr(bpy.data, i) for i in watch_list]

        self._tracking_sets = {}
        for collection in self._watch_list:
            collection_name = get_collection_name(collection)
            self._tracking_sets[collection_name] = set()

        self._old_vmat = None
        self._old_pmat = None
        self._old_viewport = None

        # Setup update functions
        for name in watch_list:
            add_func = _BaseFunc()
            update_func = _BaseFunc()
            remove_func = _BaseFunc()

            setattr(self, "add_" + name, add_func)
            setattr(self, "update_" + name, update_func)
            setattr(self, "remove_" + name, remove_func)

        def main_loop(scene):
            try:
                new_time = time.perf_counter()
                dt = new_time - self.clock
                self.clock = new_time
                self.scene_callback()
                self.processor.update(dt)
            except ReferenceError:
                bpy.app.handlers.scene_update_post.remove(main_loop)

        bpy.app.handlers.scene_update_post.append(main_loop)

        self.tex = glGenTextures(1)

    def view_update(self, context):
        """ Called when the scene is changed """
        remove_delta = {}
        add_delta = {}
        update_delta = {}

        for collection in self._watch_list:
            collection_name = get_collection_name(collection)
            collection_set = set(collection)
            tracking_set = self._tracking_sets[collection_name]

            # Check for new items
            add_method = getattr(self, "add_"+collection_name)
            add_set = collection_set - tracking_set
            add_method(add_set)
            add_delta[collection_name] = add_set
            tracking_set |= add_set

            # Check for removed items
            remove_method = getattr(self, "remove_"+collection_name)
            remove_set = tracking_set - collection_set
            remove_method(remove_set)
            remove_delta[collection_name] = remove_set
            tracking_set -= remove_set

            # Check for updates
            update_method = getattr(self, "update_"+collection_name)
            update_set = {item for item in collection if item.is_updated}
            update_method(update_set)
            update_delta[collection_name] = update_set

        def converter_callback(data):
            self.processor.process_data(data)

        self.converter.convert(add_delta, update_delta, remove_delta, converter_callback)

    def view_draw(self, context):
        """ Called when viewport settings change """
        self.override_context = context.copy()
        region = context.region
        view = context.region_data

        vmat = view.view_matrix.copy()
        vmat_inv = vmat.inverted()
        pmat = view.perspective_matrix * vmat_inv

        viewport = [region.x, region.y, region.width, region.height]

        self.update_view(vmat, pmat, viewport)

        glPushAttrib(GL_ALL_ATTRIB_BITS)

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

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, self.width, self.height, 0, GL_RGB,
            GL_UNSIGNED_BYTE, self.display.read_buffer)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

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
        #TODO: Add to converter data

        def togl(matrix):
            return [i for col in matrix.col for i in col]

        if view_matrix != self._old_vmat:
            self._old_vmat = view_matrix
            data = {"data": togl(view_matrix)}

        if projection_matrix != self._old_pmat:
            self._old_pmat = projection_matrix
            data = {"data": togl(projection_matrix)}

        if viewport != self._old_viewport:
            self._old_viewport = viewport
            data = {"width": viewport[2], "height": viewport[3]}

    def draw_callback(self):
        '''Forces a view_draw to occur'''
        view = self.override_context['region_data']
        view.view_matrix = view.view_matrix

    def scene_callback(self):
        pass
