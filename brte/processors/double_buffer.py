import ctypes


class DoubleBuffer:
    def __init__(self, size, swap_callback):
        self.read_buffer = None
        self.write_buffer = None
        self.size = 0
        self.swap_callback = swap_callback

        self.resize(size)

    def resize(self, size):
        self.read_buffer = (ctypes.c_ubyte * size)(0)
        self.write_buffer = (ctypes.c_ubyte * size)(0)
        self.size = size

    def swap(self):
        self.read_buffer, self.write_buffer = self.write_buffer, self.read_buffer
        if self.swap_callback:
            self.swap_callback()
