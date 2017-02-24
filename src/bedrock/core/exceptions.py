"""
src/core/exceptions.py the common exception classes for bedrock.
"""
from flask import jsonify


class InvalidUsage(Exception):
    """
    An exception class to represent a Bad Request
    Raise this when some property of the request is invalid
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def asserttype(obj, typ):
    """assert that obj is an instance of typ and raise an exception if not."""
    if not isinstance(obj, typ):
        msg = "%s is not of type %s" % (obj, typ)
        payload = {'obj': obj, 'type': str(typ)}
        raise InvalidUsage(msg, 400, payload)
