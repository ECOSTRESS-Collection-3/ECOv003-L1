# SYNOPSIS
#
#   AC_PROG_CYTHON()
#
# DESCRIPTION
#
#   This macro searches for a cython installation on your system. If
#   found you should call SWIG via $(CYTHON).
#
# LAST MODIFICATION

AC_DEFUN([AC_PROG_CYTHON],[
        have_cython=no
        if test "x$THIRDPARTY" = x ; then
           cython_search_path=$PATH
        else
           cython_search_path=$THIRDPARTY/bin:$PATH
        fi
        AC_PATH_PROG([CYTHON],[cython], [], [$cython_search_path])
        if test -z "$CYTHON" ; then
             AC_MSG_WARN([cannot find 'cython' program. This is only needed if you are modifying source and using maintainer mode (*not* needed to just build the system)])
             CYTHON='echo "Error: cython is not installed." ; false'
        else
	     have_cython=yes
        fi
AM_CONDITIONAL([HAVE_CYTHON], [test "$have_cython" = "yes"])
])
