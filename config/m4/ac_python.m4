# This is a replacement for ax_python_devel.html found in the standard
# autoconf archive 
# (http://www.gnu.org/software/autoconf-archive/ax_python_devel.html)
#
# The version in autoconf archive uses distutils, while apparently the
# prefered method is to use python-config program. In any case, the 
# autoconf archive version breaks on the Mac for version 2.7.5 (see 
# http://trac.macports.org/ticket/39223).
#
# AC_PYTHON_DEVEL(VERSION)
#
AC_DEFUN([AC_PYTHON_DEVEL],
[AC_ARG_VAR([PYTHON_VERSION],[The installed Python
		version to use, for example '2.3'. This string
		will be appended to the Python interpreter
		canonical name.])

AC_PATH_PROG([PYTHON],[python[$PYTHON_VERSION]], [], [$THIRDPARTY/bin:$PATH])
PYTHON_ABS=`eval echo ${PYTHON}`
PYTHON_PREFIX=`AS_DIRNAME(["$PYTHON_ABS"])`
PYTHON_PREFIX=`AS_DIRNAME(["$PYTHON_PREFIX"])`
if test -z "$PYTHON"; then
   AC_MSG_ERROR([Cannot find python$PYTHON_VERSION in your system path])
   PYTHON_VERSION=""
fi
#
# if the macro parameter ``version'' is set, honour it
#
if test -n "$1"; then
   AC_MSG_CHECKING([for a version of Python $1])
   ac_supports_python_ver=`LD_LIBRARY_PATH=$PYTHON_PREFIX/lib:$PYTHON_PREFIX/lib64 $PYTHON -c "import sys; \
	ver = sys.version.split ()[[0]]; \
	print (ver $1)"`
   if test "$ac_supports_python_ver" = "True"; then
      AC_MSG_RESULT([yes])
   else
      AC_MSG_RESULT([no])
      AC_MSG_ERROR([this package requires Python $1.
If you have it installed, but it isn't the default Python
interpreter in your system path, please pass the PYTHON_VERSION
variable to configure. See ``configure --help'' for reference.
])
      PYTHON_VERSION=""
   fi
fi

AC_MSG_CHECKING([Checking for python-config])
AC_PATH_TOOL([PYTHON_CONFIG], [python-config], [], [$THIRDPARTY/bin:$PATH])
if test -n "$PYTHON_CONFIG" ; then
    AC_MSG_RESULT([yes])
else
  AC_MSG_RESULT([no])
fi

if test -z "$PYTHON_CONFIG" ; then
  AC_MSG_ERROR([no python-config found.])
fi

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
   AC_MSG_ERROR([$PYTHON_CONFIG output is not usable])])
AC_LANG_POP([C])

CPPFLAGS="$ac_save_CPPFLAGS"
LIBS="$ac_save_LIBS"

AC_SUBST([PYTHON_VERSION])
AC_SUBST([PYTHON_CPPFLAGS])
AC_SUBST([PYTHON_LDFLAGS])

])


