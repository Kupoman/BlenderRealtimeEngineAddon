import ctypes
import math


class DummyProcessor:
    def __init__(self, buffer):
        self.buffer = buffer
        self.value = 0

    def process_data(self, data):
        pass

    def update(self, dt):
        self.value += dt
        interval = 3.0

        while self.value > interval:
            self.value -= interval
        t = self.value / interval

        t = 1.0 - (0.5 * math.cos(2 * math.pi * t) + 0.5)
        ctypes.memset(self.buffer.write_buffer, int(255*t), self.buffer.size)
        self.buffer.swap()
