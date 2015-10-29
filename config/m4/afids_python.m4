# SYNOPSIS
#
#   AFIDS_PYTHON([required], [can_build], [default_build])
#
# DESCRIPTION
#
# This either sets up to build our own version of python, or it finds
# the system python. If we use the system python, we check that the
# modules we need are also installed.
#
# A particular package might not have the library source code, so you
# can supply the "can_build" argument as "can_build". Empty string means we
# can't build this, and various help messages etc. are adjusted for this.
#
# Not finding this library might or might not indicate an error. If you
# want an error to occur if we don't find the library, then specify
# "required". Otherwise, leave it as empty and we'll just silently
# return if we don't find the library.
# 
# If the user doesn't otherwise specify the "with" argument for this
# library, we can either have a default behavior of searching for the
# library on the system or of building our own copy of it. You can
# specify "default_build" if this should build, otherwise we just look
# for this on the system.


AC_DEFUN([AFIDS_PYTHON],
[
AC_HANDLE_WITH_ARG([python], [python], [Python], $2, $3)

if test "x$want_python" = "xyes"; then
   AC_MSG_CHECKING([for python])
   succeeded=no
   if test "$build_python" == "yes"; then
     AM_PATH_PYTHON(,, [:])
     PYTHON=`pwd`"/external/python_wrap.sh" 
     PYTHON_CPPFLAGS="-I\${prefix}/include/python2.7"
     PYTHON_NUMPY_CPPFLAGS="-I\${prefix}/lib/python2.7/site-packages/numpy/core/include"
     pythondir="lib/python2.7/site-packages" 
     platpythondir="lib/python2.7/site-packages" 
     succeeded=yes
     have_python=yes
     AC_SUBST(PYTHON_CPPFLAGS)
     AC_SUBST(PYTHON_NUMPY_CPPFLAGS)
     AC_SUBST([platpythondir])
     SPHINXBUILD="\${prefix}/bin/sphinx-build"
     NOSETESTS="\${prefix}/bin/nosetests"
     AM_CONDITIONAL([HAVE_SPHINX], [true])
     AM_CONDITIONAL([HAVE_NOSETESTS], [true])
   else
     AC_PYTHON_DEVEL([>= '2.6.1'])
     AC_PYTHON_MODULE_WITH_VERSION(numpy, [1.7.0], [numpy.version.version])
     AC_PYTHON_MODULE_WITH_VERSION(scipy, [0.10.1], [scipy.version.version])
     AC_PYTHON_MODULE_WITH_VERSION(matplotlib, [1.0.1], [matplotlib.__version__])
     AC_PYTHON_MODULE(h5py, 1)
     AC_PYTHON_MODULE(sphinx, 1)
     AC_PYTHON_MODULE(sqlite3, 1)
     pythondir=`$PYTHON -c "from distutils.sysconfig import *; print get_python_lib(False,False,'')"`
     platpythondir=`$PYTHON -c "from distutils.sysconfig import *; print get_python_lib(True,False,'')"`
     PYTHON_NUMPY_CPPFLAGS=`$PYTHON -c "from numpy.distutils.misc_util import *; print '-I' + ' -I'.join(get_numpy_include_dirs())"`
     AC_SUBST([PYTHON_NUMPY_CPPFLAGS])
     AC_SUBST([platpythondir])
     AC_PROG_SPHINX
     AC_PROG_NOSETESTS
     if test -z "$NOSETESTS" ; then
        AC_MSG_ERROR(required program nosetests not found)
        exit 1
     fi     
     AC_SUBST([pkgpythondir], [\${prefix}/\${pythondir}/$PACKAGE])
     AC_SUBST(build_python)
     succeeded=yes
     have_python=yes
   fi
fi
AM_CONDITIONAL([BUILD_PYTHON], [test "$build_python" = "yes"])

AC_CHECK_FOUND([python], [python],[Python],$1,$2)

])