import bpy
import itertools
import json
import collections
import base64
import gzip
import struct

class Buffer:
    ARRAY_BUFFER = 34962
    ELEMENT_ARRAY_BUFFER = 34963

    BYTE = 5120
    UNSIGNED_BYTE = 5121
    SHORT = 5122
    UNSIGNED_SHORT = 5123
    FLOAT = 5126

    VEC3 = 'VEC3'
    VEC2 = 'VEC2'
    SCALAR = 'SCALAR'

    class Accessor:
        def __init__(self,
                     name,
                     buffer,
                     buffer_view,
                     byte_offset,
                     byte_stride,
                     component_type,
                     count,
                     type):
            self.name = name
            self.buffer = buffer
            self.buffer_view = buffer_view
            self.byte_offset = byte_offset
            self.byte_stride = byte_stride
            self.component_type = component_type
            self.count = count
            self.type = type

            if self.type == Buffer.VEC3:
                self.type_size = 3
            elif self.type == Buffer.VEC2:
                self.type_size = 2
            else:
                self.type_size = 1

            if component_type == Buffer.BYTE:
                self._ctype = '<b'
            elif component_type == Buffer.UNSIGNED_BYTE:
                self._ctype = '<B'
            elif component_type == Buffer.SHORT:
                self._ctype = '<h'
            elif component_type == Buffer.UNSIGNED_SHORT:
                self._ctype = '<H'
            elif component_type == Buffer.FLOAT:
                self._ctype = '<f'
            else:
                raise ValueError("Bad component type")

            self._ctype_size = struct.calcsize(self._ctype)
            self._buffer_data = self.buffer._get_buffer_data(self.buffer_view)

        # Inlined for performance, leaving this here as reference
        # def _get_ptr(self, idx):
            # addr = ((idx % self.type_size) * self._ctype_size + idx // self.type_size * self.byte_stride) + self.byte_offset
            # return addr

        def __len__(self):
            return self.count

        def __getitem__(self, idx):
            if not isinstance(idx, int):
                raise TypeError("Expected an integer index")

            ptr = ((idx % self.type_size) * self._ctype_size + idx // self.type_size * self.byte_stride) + self.byte_offset

            return struct.unpack_from(self._ctype, self._buffer_data, ptr)[0]

        def __setitem__(self, idx, value):
            if not isinstance(idx, int):
                raise TypeError("Expected an integer index")

            ptr = ((idx % self.type_size) * self._ctype_size + idx // self.type_size * self.byte_stride) + self.byte_offset

            struct.pack_into(self._ctype, self._buffer_data, ptr, value)

    def __init__(self, name, uri=None):
        self.name = '{}_buffer'.format(name)
        self.type = 'arraybuffer'
        self.bytelength = 0
        self.uri = uri
        self.buffer_views = collections.OrderedDict()
        self.accessors = {}

    def export_buffer(self):
        data = bytearray()
        for bn, bv in self.buffer_views.items():
            data.extend(bv['data'])
            #print(bn)

            #if bv['target'] == Buffer.ARRAY_BUFFER:
            #    idx = bv['byteoffset']
            #    while idx < bv['byteoffset'] + bv['bytelength']:
            #    	print(struct.unpack_from('<ffffff', data, idx))
            #    	idx += 24
            #if bv['target'] == Buffer.ELEMENT_ARRAY_BUFFER:
            #    idx = bv['byteoffset']
            #    while idx < bv['byteoffset'] + bv['bytelength']:
            #    	print(struct.unpack_from('<HHH', data, idx))
            #    	idx += 6

        uri = 'data:text/plain;base64,' + base64.b64encode(data).decode('ascii')
        #fname = '{}.bin'.format(self.name)
        #with open(fname, 'wb') as f:
        #    for bv in self.buffer_views.values():
        #    	f.write(bv['data'])

        #uri = 'data:text/plain;base64,'
        #with open(fname, 'rb') as f:
        #    uri += str(base64.b64encode(f.read()), 'ascii')

        return {
            'byteLength': self.bytelength,
            'type': self.type,
            'uri': uri,
        }

    def add_view(self, bytelength, target):
        buffer_name = '{}_view_{}'.format(self.name, len(self.buffer_views))
        self.buffer_views[buffer_name] = {
                'data': bytearray(bytelength),
                'target': target,
                'bytelength': bytelength,
                'byteoffset': self.bytelength,
            }
        self.bytelength += bytelength
        return buffer_name

    def export_views(self):
        gltf = {}

        for k, v in self.buffer_views.items():
            gltf[k] = {
                'buffer': self.name,
                'byteLength': v['bytelength'],
                'byteOffset': v['byteoffset'],
                'target': v['target'],
            }

        return gltf

    def _get_buffer_data(self, buffer_view):
        return self.buffer_views[buffer_view]['data']

    def add_accessor(self,
                     buffer_view,
                     byte_offset,
                     byte_stride,
                     component_type,
                     count,
                     type):
        accessor_name = '{}_accessor_{}'.format(self.name, len(self.accessors))
        self.accessors[accessor_name] = self.Accessor(accessor_name, self, buffer_view, byte_offset, byte_stride, component_type, count, type)
        return self.accessors[accessor_name]

    def export_accessors(self):
        gltf = {}

        for k, v in self.accessors.items():
            gltf[k] = {
                'bufferView': v.buffer_view,
                'byteOffset': v.byte_offset,
                'byteStride': v.byte_stride,
                'componentType': v.component_type,
                'count': v.count,
                'type': v.type,
            }

        return gltf


g_buffers = []


def togl(matrix):
    return [i for col in matrix.col for i in col]


def export_cameras(cameras):
    def export_camera(camera):
        if camera.type == 'ORTHO':
            return {
                'orthographic': {
                    'xmag': camera.ortho_scale,
                    'ymag': camera.ortho_scale,
                    'zfar': camera.clip_end,
                    'znear': camera.clip_start,
                },
                'type': 'orthographic',
            }
        else:
            return {
                'perspective': {
                    'aspectRatio': camera.angle_x / camera.angle_y,
                    'yfov': camera.angle_y,
                    'zfar': camera.clip_end,
                    'znear': camera.clip_start,
                },
                'type': 'perspective',
            }

    return {camera.name: export_camera(camera) for camera in cameras}


def export_materials(materials):
    def export_material(material):
        return {
            'instanceTechnique': {
                'technique': 'technique',
                'values': {
                    'diffuse': list((material.diffuse_color * material.diffuse_intensity)[:]) + [material.alpha],

                    'specular': list((material.specular_color * material.specular_intensity)[:]) + [material.specular_alpha],
                    'shininess': material.specular_hardness,
                    'textures': [ts.texture.image.filepath.replace('//', '') for ts in material.texture_slots if ts and ts.texture.type == 'IMAGE'],
                    'uv_layers': [ts.uv_layer for ts in material.texture_slots if ts]
                }
            }
        }
    return {material.name: export_material(material) for material in materials}

def export_meshes(meshes):
    def export_mesh(me):
        # glTF data
        gltf_mesh = {
                'name': me.name,
                'primitives': [],
            }

        me.calc_normals_split()
        me.calc_tessface()

        num_loops = len(me.loops)
        num_uv_layers = len(me.uv_layers)
        vertex_size = (3 + 3 + num_uv_layers * 2) * 4

        buf = Buffer(me.name)

        # Vertex data
        va = buf.add_view(vertex_size * num_loops, Buffer.ARRAY_BUFFER)
        vdata = buf.add_accessor(va, 0, vertex_size, Buffer.FLOAT, num_loops, Buffer.VEC3)
        ndata = buf.add_accessor(va, 12, vertex_size, Buffer.FLOAT, num_loops, Buffer.VEC3)
        tdata = [buf.add_accessor(va, 24 + 8 * i, vertex_size, Buffer.FLOAT, num_loops, Buffer.VEC2) for i in range(num_uv_layers)]

        for i, loop in enumerate(me.loops):
            vtx = me.vertices[loop.vertex_index]
            #print('row', i)
            #print('vertex', vtx.co)
            #print('normal', loop.normal)

            co = vtx.co
            normal = loop.normal

            for j in range(3):
                vdata[(i * 3) + j] = co[j]
                ndata[(i * 3) + j] = normal[j]

            for j, uv_layer in enumerate(me.uv_layers):
                tdata[j][i * 2] = uv_layer.data[i].uv.x
                tdata[j][i * 2 + 1] = uv_layer.data[i].uv.y

        prims = {ma.name if ma else '': [] for ma in me.materials}
        if not prims:
            prims = {'': []}

        # Index data
        for poly in me.polygons:
            first = poly.loop_start
            mat = me.materials[poly.material_index]
            prim = prims[mat.name if mat else '']

            if poly.loop_total == 3:
                prim += (first, first + 1, first + 2)
            elif poly.loop_total > 3:
                last = first + poly.loop_total - 1
                for i in range(first, last - 1):
                    prim += (last, i, i + 1)
            else:
                raise RuntimeError("Invalid polygon with {} vertexes.".format(poly.loop_total))

        for mat, prim in prims.items():
            ib = buf.add_view(2 * len(prim), Buffer.ELEMENT_ARRAY_BUFFER)
            idata = buf.add_accessor(ib, 0, 2, Buffer.UNSIGNED_SHORT, len(prim), Buffer.SCALAR)
            for i, v in enumerate(prim):
                idata[i] = v

            gltf_prim = {
                'attributes': {
                    'POSITION': vdata.name,
                    'NORMAL': ndata.name,
                },
                'indices': idata.name,
                'primitive': 4,
                'material': mat,
            }
            for i, v in enumerate(tdata):
                gltf_prim['attributes']['TEXCOORD_' + me.uv_layers[i].name] = v.name

            gltf_mesh['primitives'].append(gltf_prim)

        g_buffers.append(buf)
        return gltf_mesh

    return {me.name: export_mesh(me) for me in meshes}


def export_lights(lamps):
    def export_light(light):
        if light.type == 'SUN':
            return {
                'directional': {
                    'color': (light.color * light.energy)[:],
                },
                'type': 'directional',
            }
        elif light.type == 'POINT':
            return {
                'point': {
                    'color': (light.color * light.energy)[:],

                    # TODO: grab values from Blender lamps
                    'constantAttenuation': 1.0,
                    'linearAttenuation': 0.0,
                    'quadraticAttenuation': 0.0,
                },
                'type': 'point',
            }
        elif light.type == 'SPOT':
            return {
                'spot': {
                    'color': (light.color * light.energy)[:],

                    # TODO: grab values from Blender lamps
                    'constantAttenuation': 1.0,
                    'fallOffAngle': 3.14159265,
                    'fallOffExponent': 0.0,
                    'linearAttenuation': 0.0,
                    'quadraticAttenuation': 0.0,
                },
                'type': 'spot',
            }
        else:
            print("Unsupported lamp type on {}: {}".format(light.name, light.type))
            return {'type': 'unsupported'}

    gltf = {lamp.name: export_light(lamp) for lamp in lamps}

    return gltf


def export_nodes(objects):
    def export_node(obj):
        ob = {
            'name': obj.name,
            'children': [child.name for child in obj.children],
            'matrix': togl(obj.matrix_world),
        }

        if obj.type == 'MESH':
            ob['meshes'] = [obj.data.name]
        elif obj.type == 'LAMP':
            ob['light'] = obj.data.name
        elif obj.type == 'CAMERA':
            ob['camera'] = obj.data.name

        return ob

    return {obj.name: export_node(obj) for obj in objects}


def export_scenes(scenes):
    def export_scene(scene):
        return {
            'nodes': [ob.name for ob in scene.objects],
            'background_color': scene.world.horizon_color[:],
            'active_camera': scene.camera.name,
        }

    return {scene.name: export_scene(scene) for scene in scenes}


def export_buffers():
    gltf = {
        'buffers': {},
        'bufferViews': {},
        'accessors': {},
    }

    for buf in g_buffers:
        gltf['buffers'][buf.name] = buf.export_buffer()
        gltf['bufferViews'].update(buf.export_views())
        gltf['accessors'].update(buf.export_accessors())

    return gltf


def export_gltf(scene_delta):
    global g_buffers

    gltf = {
        'cameras': export_cameras(scene_delta.get('cameras', [])),
        'materials': export_materials(scene_delta.get('materials', [])),
        'meshes': export_meshes(scene_delta.get('meshes', [])),
        'lights': export_lights(scene_delta.get('lamps', [])),
        'nodes': export_nodes(scene_delta.get('objects', [])),
        'scene': bpy.context.scene.name,
        'scenes': export_scenes(scene_delta.get('scenes', [])),

        # TODO
        'animations': {},
        'asset': {},
        'images': {},
        'programs': {},
        'samplers': {},
        'shaders': {},
        'skins': {},
        'techniques': {},
        'textures': {},
    }

    gltf.update(export_buffers())
    g_buffers = []

    return gltf


if __name__ == '__main__':
    with open('dump.gltf', 'w') as f:
        json.dump(export_gltf, f, indent=4)
