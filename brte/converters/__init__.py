BTFConverter = None

def alias():
    global BTFConverter
    BTFConverter = btf.BTFConverter


if '__imported__' in locals():
    import imp
    imp.reload(btf)
    alias()
else:
    __imported__ = True
    from . import btf
    alias()
