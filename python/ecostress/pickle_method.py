# Provide support for pickling a method. See
# https://bytes.com/topic/python/answers/552476-why-cant-you-pickle-instancemethods#edit2155350

import copyreg
import types


def _pickle_method(method):
    func_name = method.__func__.__name__
    obj = method.__self__
    cls = method.__self__.__class__
    return _unpickle_method, (func_name, obj, cls)


def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)


copyreg.pickle(types.MethodType, _pickle_method)

__all__: list[str] = []
