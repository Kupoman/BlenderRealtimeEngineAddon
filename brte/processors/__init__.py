DoubleBuffer = None
DummyProcessor = None

def alias():
    global DoubleBuffer, DummyProcessor
    DoubleBuffer = double_buffer.DoubleBuffer
    DummyProcessor = dummy.DummyProcessor


if '__imported__' in locals():
    import imp
    imp.reload(double_buffer)
    imp.reload(dummy)
    alias()
else:
    __imported__ = True
    from . import double_buffer
    from . import dummy
    alias()
