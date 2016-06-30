#####
#
# SYNOPSIS
#
#   AC_PROG_PYTEST()
#
# DESCRIPTION
#
#   This macro searches for a Python Pytest installation on your system. If
#   found you should call pytest via $(PYTEST). 
#
#   In configure.in, use as:
#
#     AC_PROG_PYTEST
#

AC_DEFUN([AC_PROG_PYTEST],[
        have_pytest=no
        AC_ARG_VAR([PYTEST], [Override the pytest executable to use,
           the default is just 'py.test'])
        if test "$PYTEST" == ""; then
           PYTEST=py.test
        fi
        AC_PATH_PROG([PYTEST],[$PYTEST], [], [$python_search_path])
        if test -z "$PYTEST" ; then
           AC_MSG_WARN([cannot find 'py.test' program.])
           PYTEST='echo "Error: pytest is not installed. " ; false'
        else
          have_pytest=yes
        fi
AM_CONDITIONAL([HAVE_PYTEST], [test "$have_pytest" = "yes"])
])
