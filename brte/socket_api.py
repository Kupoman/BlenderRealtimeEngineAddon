import enum
import json
import socket
import struct
import sys
import time


class AutoNumber(enum.Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


class MethodIDs(AutoNumber):
    __order__ = "add update remove"
    add = ()
    update = ()
    remove = ()


class DataIDs(AutoNumber):
    __order__ = "view projection viewport gltf"
    view = ()
    projection = ()
    viewport = ()
    gltf = ()


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


class SocketClient(object):
    def __init__(self, handler):
        self.handler = handler

        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.connect(("127.0.0.1", 4242))

    def run(self):
        try:
            while True:
                try:
                    self.socket.setblocking(False)
                    message = self.socket.recv(1)
                    if message:
                        self.socket.setblocking(True)
                        method_id, data_id = decode_cmd_message(message)
                        size = decode_size_message(self.socket.recv(4))
    
                        data = b""
                        remaining = size
                        while remaining > 0:
                            chunk = self.socket.recv(min(1024, remaining))
                            remaining -= len(chunk)
                            data += chunk
                        data = json.loads(data.decode())
                        if data_id == DataIDs.projection:
                            if hasattr(self.handler, 'handle_projection'):
                                self.handler.handle_projection(data['data'])
                        elif data_id == DataIDs.view:
                            if hasattr(self.handler, 'handle_view'):
                                self.handler.handle_view(data['data'])
                        elif data_id == DataIDs.viewport:
                            if hasattr(self.handler, 'handle_viewport'):
                                self.handler.handle_viewport(data['width'], data['height'])
                        elif data_id == DataIDs.gltf:
                            if hasattr(self.handler, 'handle_gltf'):
                                self.handler.handle_gltf(data)
                except socket.error:
                    break
    
            # Return output
            img_data, sx, sy = self.handler.get_render_image()
            data_size = len(img_data)
            self.socket.setblocking(True)
            try:
                self.socket.send(struct.pack("HH", sx, sy))

                start_time = time.clock()
                sent_count = 0

                while sent_count < data_size:
                    sent_count += self.socket.send(img_data[sent_count:data_size - sent_count])
                etime = time.clock() - start_time
                tx = 0 if etime == 0 else sent_count*8/1024/1024/etime
                #print("Sent %d bytes in %.2f ms (%.2f Mbps)" % (sent_count, etime*1000, tx))
            except socket.timeout:
                print("Failed to send result data")
        except socket.error as e:
            print("Closing")
            self.socket.close()
            sys.exit()
