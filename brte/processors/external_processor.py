import ctypes
import json
import socket
import struct
import subprocess
import time


MSG_DATA = 0
MSG_UPDATE = 1


class ExternalProcessor:
    def __init__(self, command, port=5555):
        self.width = 1
        self.height = 1
        self.buffer = (ctypes.c_ubyte * 3)(0)
        self.value = 0
        self.is_connected = False

        self.process = subprocess.Popen(command)

        self.listen_socket = socket.socket()
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 6 * 2**25)
        self.listen_socket.bind(('localhost', port))
        self.listen_socket.listen(3)
        self.listen_socket.settimeout(5)

    def destroy(self):
        self.listen_socket.close()
        if self.is_connected:
            self.socket.close()

        self.process.kill()

    def _connect(self):
        if not self.is_connected:
            try:
                self.socket = self.listen_socket.accept()[0]
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 6 * 2**20)
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.socket.settimeout(3)
                self.is_connected = True
                print('Connected to external process')
            except:
                print('Unable to connect to external process')

    def process_data(self, data):
        '''Accept converted data to be consumed by the processor'''
        self._connect()
        if not self.is_connected:
            return

        payload = json.dumps(data, check_circular=False).encode('ascii')

        self.socket.send(struct.pack('=HI', MSG_DATA, len(payload)))
        self.socket.send(payload)
        self.socket.recv(1)

    def update(self, timestep):
        '''Advance the processor by the timestep and update the viewport image'''
        self._connect()
        if not self.is_connected:
            return None

        self.socket.send(struct.pack('=Hf', MSG_UPDATE, timestep))

        start = time.perf_counter()
        width, height = struct.unpack('=HH', self.socket.recv(4))
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self.buffer = (ctypes.c_ubyte * (self.width * self.height * 3))()

        data_size = self.width*self.height*3
        remaining = data_size
        view = memoryview(self.buffer)
        while remaining > 0:
            rcv_size = self.socket.recv_into(view, remaining)
            view = view[rcv_size:]
            remaining -= rcv_size

        transfer_t = time.perf_counter() - start
        # print('Blender: Update time: {}ms'.format(transfer_t * 1000))
        # print('Blender: Speed: {} Gbit/s'.format(data_size/1024/1024/1024*8 / transfer_t))

        return ctypes.byref(self.buffer)
