# This file was automatically generated by SWIG (https://www.swig.org).
# Version 4.3.1
#
# Do not make changes to this file unless you know what you are doing - modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
from ._swig_wrap import _geometric_model_image_handle_fill

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

_swig_new_instance_method = _geometric_model_image_handle_fill.SWIG_PyInstanceMethod_New
_swig_new_static_method = _geometric_model_image_handle_fill.SWIG_PyStaticMethod_New

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "this":
            set(self, name, value)
        elif name == "thisown":
            self.this.own(value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):
    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)
    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""
    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())
    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)


import weakref

SWIG_MODULE_ALREADY_DONE = _geometric_model_image_handle_fill.SWIG_MODULE_ALREADY_DONE
class SwigPyIterator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined - class is abstract")
    __repr__ = _swig_repr
    __swig_destroy__ = _geometric_model_image_handle_fill.delete_SwigPyIterator
    value = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_value)
    incr = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_incr)
    decr = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_decr)
    distance = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_distance)
    equal = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_equal)
    copy = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_copy)
    next = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_next)
    __next__ = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator___next__)
    previous = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_previous)
    advance = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator_advance)
    __eq__ = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator___eq__)
    __ne__ = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator___ne__)
    __iadd__ = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator___iadd__)
    __isub__ = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator___isub__)
    __add__ = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator___add__)
    __sub__ = _swig_new_instance_method(_geometric_model_image_handle_fill.SwigPyIterator___sub__)
    def __iter__(self):
        return self

# Register SwigPyIterator in _geometric_model_image_handle_fill:
_geometric_model_image_handle_fill.SwigPyIterator_swigregister(SwigPyIterator)
SHARED_PTR_DISOWN = _geometric_model_image_handle_fill.SHARED_PTR_DISOWN

import os

def _new_from_init(cls, version, *args):
    '''For use with pickle, covers common case where we just store the
    arguments needed to create an object. See for example HdfFile'''
    if(cls.pickle_format_version() != version):
      raise RuntimeException("Class is expecting a pickled object with version number %d, but we found %d" % (cls.pickle_format_version(), version))
    inst = cls.__new__(cls)
    inst.__init__(*args)
    return inst

def _new_from_serialization(data):
    return geocal_swig.serialize_function.serialize_read_binary(data)

def _new_from_serialization_dir(dir, data):
    curdir = os.getcwd()
    try:
      os.chdir(dir)
      return geocal_swig.serialize_function.serialize_read_binary(data)
    finally:
      os.chdir(curdir)


def _new_vector(cls, version, lst):
    '''Create a vector from a list.'''
    if(cls.pickle_format_version() != version):
      raise RuntimeException("Class is expecting a pickled object with version number %d, but we found %d" % (cls.pickle_format_version(), version))
    inst = cls.__new__(cls)
    inst.__init__()
    for i in lst:
       inst.append(i)
    return inst

def _new_from_set(cls, version, *args):
    '''For use with pickle, covers common case where we use a set function 
    to assign the value'''
    if(cls.pickle_format_version() != version):
      raise RuntimeException("Class is expecting a pickled object with version number %d, but we found %d" % (cls.pickle_format_version(), version))
    inst = cls.__new__(cls)
    inst.__init__()
    inst.set(*args)
    return inst

import geocal_swig.calc_raster
import geocal_swig.raster_image_variable
import geocal_swig.raster_image
import geocal_swig.generic_object
import geocal_swig.with_parameter
import geocal_swig.geocal_exception
import geocal_swig.observer
class GeometricModelImageHandleFill(geocal_swig.calc_raster.CalcRaster):
    r"""

    Variation of GeoCal::GeometricModelImage that handles fill data.

    C++ includes: geometric_model_image_handle_fill.h 
    """

    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, Data, Geom_model, Number_line, Number_sample, Fill_value=0.0):
        r"""

        Ecostress::GeometricModelImageHandleFill::GeometricModelImageHandleFill(const boost::shared_ptr< GeoCal::RasterImage > &Data, const
        boost::shared_ptr< GeoCal::GeometricModel > &Geom_model, int
        Number_line, int Number_sample, double Fill_value=0.0)
        Ecostress::GeometricModelImageHandleFill::GeometricModelImageHandleFil
        l
        Constructor.
        This takes underlying data, and a geometric model to use to resample
        it.

        Because we fill in data outside of the original image with O's this
        image can be any size. So the size desired needs to be passed in. 
        """
        _geometric_model_image_handle_fill.GeometricModelImageHandleFill_swiginit(self, _geometric_model_image_handle_fill.new_GeometricModelImageHandleFill(Data, Geom_model, Number_line, Number_sample, Fill_value))
    _v_raw_data = _swig_new_instance_method(_geometric_model_image_handle_fill.GeometricModelImageHandleFill__v_raw_data)

    @property
    def raw_data(self):
        return self._v_raw_data()

    _v_geometric_model = _swig_new_instance_method(_geometric_model_image_handle_fill.GeometricModelImageHandleFill__v_geometric_model)

    @property
    def geometric_model(self):
        return self._v_geometric_model()

    _v_fill_value = _swig_new_instance_method(_geometric_model_image_handle_fill.GeometricModelImageHandleFill__v_fill_value)

    @property
    def fill_value(self):
        return self._v_fill_value()


    def __reduce__(self):
    #Special handling for when we are doing boost serialization, we set
    #"this" to None
      if(self.this is None):
        return super().__reduce__()
      return _new_from_serialization, (geocal_swig.serialize_function.serialize_write_binary(self),)

    __swig_destroy__ = _geometric_model_image_handle_fill.delete_GeometricModelImageHandleFill

# Register GeometricModelImageHandleFill in _geometric_model_image_handle_fill:
_geometric_model_image_handle_fill.GeometricModelImageHandleFill_swigregister(GeometricModelImageHandleFill)

__all__ = ["GeometricModelImageHandleFill"]


