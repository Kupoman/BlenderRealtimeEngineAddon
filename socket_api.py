import enum
import json
import socket
import struct


class AutoNumber(enum.Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


class MethodIDs(AutoNumber):
    add = ()
    update = ()
    remove = ()


class DataIDs(AutoNumber):
    view = ()
    projection = ()
    viewport = ()

    actions = ()
    armatures = ()
    cameras = ()
    images = ()
    lamps = ()
    materials = ()
    meshes = ()
    objects = ()
    scenes = ()
    sounds = ()
    speakers = ()
    textures = ()
    worlds = ()


def send_message(_socket, method, data_id, data):
    _socket.setblocking(True)
    _socket.settimeout(1)

    attempts = 3
    while attempts > 0:
        message = encode_cmd_message(method, data_id)
        try:
            _socket.send(message)
            data_str = json.dumps(data)
            _socket.send(struct.pack("I", len(data_str)))
            _socket.send(data_str.encode())
        except socket.timeout:
            attempts -= 1
            continue

        break
    else:
        print("Failed to send message (%s, %s)." % (method.name, data_id.name))

    _socket.setblocking(False)


def encode_cmd_message(method_id, data_id):
    message = data_id.value & 0b00001111
    message |= method_id.value << 4
    return struct.pack("B", message)


def decode_cmd_message(message):
    message = struct.unpack('B', message)[0]
    method_id = message >> 4
    data_id = message & 0b00001111
    return MethodIDs(method_id), DataIDs(data_id)


def decode_size_message(message):
    return struct.unpack('I', message)[0]