//--------------------------------------------------------------
// This provides common functions etc. used throughout our SWIG
// code. This should get included at the top of each swig file.
//--------------------------------------------------------------

// The module actually gets overridden by SWIG command line options
// when we build. But we still need to supply this to get the
// directors=1 and allprotected=1 set.

//
// See https://github.com/swig/swig/issues/2260 for discussion of
// moduleimport, this is needed because we place everything in one
// library _swig_wrap.so. Swig 4 seems to prefer splitting this into
// separate libraries (so for example "exception.py" would import
// _exception.so). It is possible we can change to that in the future,
// although it seems like it is useful to have it all one library like
// things like cython do. But for now we can just work around this.
// The effect of this is just to change the "import" line in the swig
// generated python code.

#if SWIG_VERSION < 0x040000
%module(directors="1", allprotected="1") foo
#else
%module(moduleimport="from ._swig_wrap import $module", directors="1", allprotected="1") foo
#endif

%include "geocal_common.i"

// Short cut for ingesting a base class
%define %ecostress_base_import(NAME)
%import(module="ecostress_swig.NAME") "NAME.i"
%enddef

%define %geocal_base_import(NAME)
%import(module="geocal_swig.NAME") "NAME.i"
%enddef

%define %ecostress_shared_ptr(TYPE...)
%geocal_shared_ptr(TYPE)
%enddef
