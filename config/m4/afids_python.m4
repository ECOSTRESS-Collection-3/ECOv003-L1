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
# Guard against running twice
if test "x$done_python" = "x"; then
AC_HANDLE_WITH_ARG([python], [python], [Python], $2, $3, $1)
if test "x$want_python" = "xyes"; then
   AC_MSG_CHECKING([for python])
   succeeded=no
   if test "$build_python" == "yes"; then
     AM_PATH_PYTHON(,, [:])
     # Will need to update this if we change the version we are building
     python_inc_path=python3.9m
     python_lib_path=python3.9
     PYTHON=`pwd`"/external/python_wrap.sh" 
     PYTHON_CPPFLAGS="-I\${prefix}/include/${python_inc_path}"
     PYTHON_NUMPY_CPPFLAGS="-I\${prefix}/lib/${python_lib_path}/site-packages/numpy/core/include"
     pythondir="lib/${python_lib_path}/site-packages" 
     platpythondir="lib/${python_lib_path}/site-packages" 
     succeeded=yes
     have_python=yes
     AC_SUBST(PYTHON_CPPFLAGS)
     AC_SUBST(PYTHON_NUMPY_CPPFLAGS)
     AC_SUBST([platpythondir])
     SPHINXBUILD="\${prefix}/bin/sphinx-build"
     PYTEST="\${prefix}/bin/py.test"
     PYTHON_LDPATH=""
     AC_SUBST(PYTHON_LDPATH)
     AM_CONDITIONAL([HAVE_SPHINX], [true])
     AM_CONDITIONAL([HAVE_PYTEST], [true])
   else
     if test "$1" == "required"; then
        if test "x$PYTHON" = "x" -a "x$ac_python_path" != "x"; then
            PYTHON=$ac_python_path
	fi
	AC_PYTHON_DEVEL([3.4.0])
	old_ld_library_path="$LD_LIBRARY_PATH"
	PYTHON_LDPATH=$PYTHON_PREFIX/lib:$PYTHON_PREFIX/lib64:
	export LD_LIBRARY_PATH=$PYTHON_LDPATH$LD_LIBRARY_PATH
        AC_PYTHON_MODULE_WITH_VERSION(numpy, [1.7.0], [numpy.version.version], [required])
        AC_PYTHON_MODULE_WITH_VERSION(scipy, [0.10.1], [scipy.version.version], [required])
        AC_PYTHON_MODULE_WITH_VERSION(matplotlib, [1.0.1], [matplotlib.__version__], [required])
	
        AC_PYTHON_MODULE_WITH_VERSION(h5py, , , [not_required])
        AC_PYTHON_MODULE_WITH_VERSION(sphinx, , , [required])
        AC_PYTHON_MODULE_WITH_VERSION(sqlite3, , , [required])
	if test "x$PYTHON" != "x"; then
          pythondir=`$PYTHON -c "from distutils.sysconfig import *; print(get_python_lib(False,False,''))"`
          platpythondir=`$PYTHON -c "from distutils.sysconfig import *; print(get_python_lib(True,False,''))"`
          PYTHON_NUMPY_CPPFLAGS=`$PYTHON -c "from numpy.distutils.misc_util import *; print('-I' + ' -I'.join(get_numpy_include_dirs()))"`
	fi
	LD_LIBRARY_PATH=$old_ld_library_path
        AC_SUBST([PYTHON_NUMPY_CPPFLAGS])
        AC_SUBST([platpythondir])
        AC_PROG_SPHINX
        AC_PROG_PYTEST
        if test "x$have_pytest" != "xyes" ; then
           AC_MSG_WARN(required program py.test not found)
           PYTHON=""
        fi
        if test "x$PYTHON" != "x"; then
          AC_SUBST([pkgpythondir], [\${prefix}/\${pythondir}/$PACKAGE])
          AC_SUBST(build_python)
          AC_SUBST(PYTHON_LDPATH)
          succeeded=yes
          have_python=yes
	fi
    else
        if test "x$PYTHON" = "x" -a "x$ac_python_path" != "x"; then
            PYTHON=$ac_python_path
	fi
        AC_PYTHON_DEVEL([>= '3.4.0'])
        if test "x$PYTHON" != "x"; then
           pythondir=`$PYTHON -c "from distutils.sysconfig import *; print(get_python_lib(False,False,''))"`
           platpythondir=`$PYTHON -c "from distutils.sysconfig import *; print(get_python_lib(True,False,''))"`
           AC_SUBST([platpythondir])
   	   AM_CONDITIONAL([HAVE_SPHINX], [false])
           AM_CONDITIONAL([HAVE_PYTEST], [false])
           succeeded=yes
           have_python=no
	fi
    fi
   fi
fi
if test "$succeeded" != "yes" -a "x$build_needed_python" == "xyes" ; then
     build_python="yes"
     ac_python_path="\${prefix}"
     AM_PATH_PYTHON(,, [:])
     # Will need to update this if we change the version we are building
     python_inc_path=python3.9m
     python_lib_path=python3.9
     PYTHON=`pwd`"/external/python_wrap.sh" 
     PYTHON_CPPFLAGS="-I\${prefix}/include/${python_inc_path}"
     PYTHON_NUMPY_CPPFLAGS="-I\${prefix}/lib/${python_lib_path}/site-packages/numpy/core/include"
     PYTHON_LDPATH="\${prefix}/lib:\${prefix}/lib64:"
     pythondir="lib/${python_lib_path}/site-packages" 
     platpythondir="lib/${python_lib_path}/site-packages" 
     succeeded=yes
     have_python=yes
     AC_SUBST(PYTHON_CPPFLAGS)
     AC_SUBST(PYTHON_NUMPY_CPPFLAGS)
     AC_SUBST(PYTHON_LDPATH)
     AC_SUBST([platpythondir])
     SPHINXBUILD="\${prefix}/bin/sphinx-build"
     PYTEST="\${prefix}/bin/py.test"
     AM_CONDITIONAL([HAVE_SPHINX], [true])
     AM_CONDITIONAL([HAVE_PYTEST], [true])
fi

AM_CONDITIONAL([BUILD_PYTHON], [test "$build_python" = "yes"])

AC_CHECK_FOUND([python], [python],[Python],$1,$2)

done_python="yes"
fi
])
