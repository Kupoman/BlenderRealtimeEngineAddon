'''An example module demonstrating the implementation of a processor'''
import ctypes
import math


class DummyProcessor:
    '''An example processor that simply changes the viewport color'''

    def __init__(self, buffer):
        '''Construct a DummyProcessor with a buffer for drawing into'''

        self.buffer = buffer
        self.value = 0

    def process_data(self, data):
        '''Accept converted data to be consumed by the processor'''
        pass

    def update(self, timestep):
        '''Advance the processor by the timestep and update the viewport image'''

        self.value += timestep
        interval = 3.0

        while self.value > interval:
            self.value -= interval
        alpha = self.value / interval

        alpha = 1.0 - (0.5 * math.cos(2 * math.pi * alpha) + 0.5)
        ctypes.memset(self.buffer.write_buffer, int(255*alpha), self.buffer.size)
        self.buffer.swap()
