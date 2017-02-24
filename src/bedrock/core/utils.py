"""
    Utility functions for bedrock
"""
def get_class(classname):
    modulename = classname.rpartition(".")[0]
    import importlib
    m = importlib.import_module(modulename)
    objectname = "m.%s" % (classname.rpartition(".")[2])
    mod = eval(objectname)()
    return mod
