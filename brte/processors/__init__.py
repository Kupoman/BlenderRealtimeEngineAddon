DoubleBuffer = None
DummyProcessor = None
ExternalProcessor = None

def alias():
    global DoubleBuffer, DummyProcessor, ExternalProcessor
    DoubleBuffer = double_buffer.DoubleBuffer
    DummyProcessor = dummy.DummyProcessor
    ExternalProcessor = external_processor.ExternalProcessor

if '__imported__' in locals():
    import imp
    imp.reload(double_buffer)
    imp.reload(external_processor)
    imp.reload(dummy)
    alias()
else:
    __imported__ = True
    from . import double_buffer
    from . import external_processor
    from . import dummy
    alias()
