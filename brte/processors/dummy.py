'''An example module demonstrating the implementation of a processor'''
import ctypes
import math


class DummyProcessor:
    '''An example processor that simply changes the viewport color'''

    def __init__(self):
        '''Construct a DummyProcessor with a buffer for drawing into'''

        self.value = 0
        self.buffer = (ctypes.c_ubyte * 3)(0)

    def process_data(self, data):
        '''Accept converted data to be consumed by the processor'''
        pass

    def destroy(self):
        '''Cleanup function called when the processor is no longer needed'''
        pass

    def update(self, timestep):
        '''Advance the processor by the timestep and update the viewport image'''

        self.value += timestep
        interval = 3.0

        while self.value > interval:
            self.value -= interval
        alpha = self.value / interval

        alpha = 1.0 - (0.5 * math.cos(2 * math.pi * alpha) + 0.5)
        ctypes.memset(self.buffer, int(255*alpha), 3)

        return ctypes.byref(self.buffer)
