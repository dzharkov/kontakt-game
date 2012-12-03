import functools

def exec_once(callback):
    @functools.wraps(callback)
    def inner(*args, **kwargs):
        try:
            return inner._once_result
        except AttributeError:
            inner._once_result = callback(*args, **kwargs)
            return inner._once_result
    return inner