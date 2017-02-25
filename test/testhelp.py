"""Helper functions for writing unit tests"""

def expects(status_code, msg):
    """A decorator that runs a function asserting an HTTP status code print msg if assert fails.
    Arguments are passed to the inner function.

    Example:

    @expects(200, "examplefunc failed")
    def examplefunc(url, kwarg=True):
        return requests.get(url)

    will raise an assertion error if it doesn't get a 200 OK response
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            resp = func(*args, **kwargs)
            assert resp.status_code == status_code, msg
            return resp
        return wrapper
    return decorator

def is_numeric(nptype):
    """Test is a numpy test is numeric"""
    name = nptype.name
    return 'float' in name or 'int' in name or 'long' in name or 'complex' in name

def column_types(dataframe):
    """get a list of the column types for a dataframe."""
    columntypes = []
    for i, typ in enumerate(dataframe.dtypes.tolist()):
        if is_numeric(typ):
            columntypes.append('Numeric')
        elif typ.name == 'object':
            if typ.name == 'str' or isinstance(dataframe.ix[0, i], str):
                columntypes.append('String')
    return columntypes
