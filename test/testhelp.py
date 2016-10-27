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
