"""
Classes that capture the bedrock state.
"""
import socket
from collections import Mapping

class Storable(object):
    """An object that can be stored into a MongoDB instance or sent over the wire in JSON formant"""
    def dict(self):
        """return this object as a dictionary for the purpose of serialization"""
        return self.__dict__
    def __repr__(self):
        for key, val in self.dict():
            print("%s: %s," % (key, val))

def none2empty(obj):
    """
    returns obj unless it is None, then return empty list.
    Useful for defaulting to an empty list
    """
    if obj is not None:
        return obj
    else:
        return []

class Source(Storable):
    """A class for representing a bedrock source."""
    def __init__(self, name, rootdir, src_id, src_type, time,
                 ingest_id, group_name, matrices=None,
                 status=None, count=0, stash=None):
        self.name = name
        self.host = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                     if not ip.startswith("127.")][-1]
        self.rootdir = rootdir
        self.src_id = src_id
        self.src_type = src_type
        self.created = time
        self.ingest_id = ingest_id
        self.matrices = none2empty(matrices)
        self.status = none2empty(status)
        self.count = count
        self.stash = none2empty(stash)
        self.group_name = group_name

class SourceCreated(Storable):
    """A class that gets sent back on creation of a Source on the bedrock server"""
    def __init__(self, source):
        self.name = source.name
        self.host = source.host
        self.rootdir = source.rootdir
        self.src_id = source.src_id
        self.src_type = source.src_type
        self.created = source.created
        self.matrices_count = len(source.matrices)
