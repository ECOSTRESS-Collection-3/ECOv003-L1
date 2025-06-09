# This is a replacement for ax_python_devel.html found in the standard
# autoconf archive 
# (http://www.gnu.org/software/autoconf-archive/ax_python_devel.html)
#
# The version in autoconf archive uses distutils, while apparently the
# prefered method is to use python-config program. In any case, the 
# autoconf archive version breaks on the Mac for version 2.7.5 (see 
# http://trac.macports.org/ticket/39223).
#
# If python isn't found, then PYTHON will be an empty string. Otherwise
# it will be set to the location of python.
#
# AC_PYTHON_DEVEL(VERSION)
#
AC_DEFUN([AC_PYTHON_DEVEL],
[AC_ARG_VAR([PYTHON_VERSION],[The installed Python
		version to use, for example '2.3'. This string
		will be appended to the Python interpreter
		canonical name.])

if test "x$THIRDPARTY" = x ; then
   python_search_path=$PATH
else
   python_search_path=$THIRDPARTY/bin:$PATH
fi
if test "x$CONDA_PREFIX" != x ; then
   python_search_path=$CONDA_PREFIX/bin:$python_search_path
fi
AC_PATH_PROG([PYTHON],[python[$PYTHON_VERSION]], [], [$python_search_path])
PYTHON_ABS=`eval echo ${PYTHON}`
PYTHON_PREFIX=`AS_DIRNAME(["$PYTHON_ABS"])`
PYTHON_PREFIX=`AS_DIRNAME(["$PYTHON_PREFIX"])`
if test -z "$PYTHON"; then
   AC_MSG_WARN([Cannot find python$PYTHON_VERSION in your system path])
   PYTHON_VERSION=""
fi

#
# if the macro parameter ``version'' is set, honour it
#
if test -n "$1" -a "x$PYTHON" != "x"; then
   AC_MSG_CHECKING([for a version of Python $1])
   ac_supports_python_ver=`LD_LIBRARY_PATH=$PYTHON_PREFIX/lib:$PYTHON_PREFIX/lib64:$LD_LIBRARY_PATH $PYTHON -c "import sys; from distutils.version import LooseVersion; \
	ver = sys.version.split ()[[0]]; \
	print (LooseVersion(ver) >= LooseVersion('$1'))"`
   if test "$ac_supports_python_ver" = "True"; then
      AC_MSG_RESULT([yes])
   else
      AC_MSG_RESULT([no])
      AC_MSG_WARN([this package requires Python $1.
If you have it installed, but it isn't the default Python
interpreter in your system path, please pass the PYTHON_VERSION
variable to configure. See ``configure --help'' for reference.
])
      PYTHON=""
      PYTHON_VERSION=""
   fi
fi

if test "x$PYTHON" != "x"; then
  AC_MSG_CHECKING([Checking for python-config])
  ac_python_config_name=`LD_LIBRARY_PATH=$PYTHON_PREFIX/lib:$PYTHON_PREFIX/lib64:$LD_LIBRARY_PATH $PYTHON -c 'import sys; import os; print("%s-config" % os.path.basename(os.path.realpath(sys.executable)))'`
  AC_PATH_TOOL([PYTHON_CONFIG], [$ac_python_config_name], [], [$python_search_path])
  if test -n "$PYTHON_CONFIG" ; then
      AC_MSG_RESULT([yes])
  else
    AC_MSG_RESULT([no])
  fi

  if test -z "$PYTHON_CONFIG" ; then
    AC_MSG_WARN([no python-config found.])
    PYTHON=""
  fi
fi

if test "x$PYTHON" != "x"; then
  PYTHON_CPPFLAGS="$("$PYTHON_CONFIG" --includes)"
  PYTHON_LDFLAGS="$("$PYTHON_CONFIG" --ldflags)"

  ac_save_CPPFLAGS="$CPPFLAGS"
  ac_save_LIBS="$LIBS"
  CPPFLAGS="$LIBS $PYTHON_CPPFLAGS"
  LIBS="$LIBS $PYTHON_LIBS"
  AC_MSG_CHECKING([Checking if python-config results are accurate])
  AC_LANG_PUSH([C])
  AC_LINK_IFELSE([
    AC_LANG_PROGRAM([[#include <Python.h>]],
                    [[Py_Initialize();]])
    ],
    [AC_MSG_RESULT([yes])]
    [AC_MSG_RESULT([no])
     AC_MSG_WARN([$PYTHON_CONFIG output is not usable])
     PYTHON=""])
  AC_LANG_POP([C])

  CPPFLAGS="$ac_save_CPPFLAGS"
  LIBS="$ac_save_LIBS"

  AC_SUBST([PYTHON_VERSION])
  AC_SUBST([PYTHON_CPPFLAGS])
  AC_SUBST([PYTHON_LDFLAGS])
fi
])


