# SYNOPSIS
#
#   AC_DOXYGEN([required], [can_build], [default_build])
#
# DESCRIPTION
#
# This looks for the doxygen. If we find it, then we set the
# Makefile conditional HAVE_DOXYGEN. We also set DOXYGEN to the command.
#
# To allow users to build there own copy of Doxygen, we also define
# BUILD_DOXYGEN.
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

AC_DEFUN([AC_DOXYGEN],
[
# Guard against running twice
if test "x$done_doxygen" = "x"; then
AC_HANDLE_WITH_ARG([doxygen], [doxygen], [Doxygen], $2, $3, $1)

if test "x$want_doxygen" = "xyes"; then
        AC_MSG_CHECKING([for Doxygen])
        succeeded=no
        if test "$ac_doxygen_path" != ""; then
            succeeded=yes
	    DOXYGEN=$ac_doxygen_path/bin/doxygen
        else
	    if test "x$THIRDPARTY" = x ; then
              doxygen_search_path=$PATH
            else
              doxygen_search_path=$THIRDPARTY/bin:$PATH
            fi
	    if test "x$CONDA_PREFIX" != x ; then
              doxygen_search_path=$CONDA_PREFIX/bin:$doxygen_search_path
	    fi
            AC_PATH_PROG([DOXYGEN], [doxygen], [], [$doxygen_search_path])
	    if test -n "$DOXYGEN" ; then
              succeeded=yes
            fi
        fi
	if test "$succeeded" != "yes" -a "x$build_needed_doxygen" == "xyes" ; then
            build_doxygen="yes"
            ac_doxygen_path="\${prefix}"
	    DOXYGEN=$ac_doxygen_path/bin/doxygen
            succeeded=yes
        fi

        if test "$succeeded" != "yes" ; then
                AC_MSG_RESULT([no])
        else
                AC_MSG_RESULT([yes])
                AC_SUBST(DOXYGEN)
                have_doxygen="yes"
        fi
fi
AM_CONDITIONAL([HAVE_DOXYGEN], [test "$have_doxygen" = "yes"])
AM_CONDITIONAL([BUILD_DOXYGEN], [test "$build_doxygen" = "yes"])

AC_CHECK_FOUND([doxygen], [doxygen],[Doxygen],$1,$2)

done_doxygen="yes"
fi
])
