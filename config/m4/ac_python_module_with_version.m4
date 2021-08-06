# SYNOPSIS
#
#   AC_PYTHON_MODULE_WITH_VERSION(modname, required_version, module version, is_required)
#
# Variation of AC_PYTHON_MODULE that also tests the version of a module.
#
# We only check if PYTHON is defined, and if we fail then we set PYTHON
# to an empty string.
#
# If you leave the verison of, then any version is allowed.


AC_DEFUN([AC_PYTHON_MODULE_WITH_VERSION],[
    if test "x$PYTHON" != "x"; then
      PYTHON_NAME=`basename $PYTHON`
      AC_MSG_CHECKING($PYTHON_NAME module: $1)
          if test -n "$3"
	  then
   	     $PYTHON -c "import $1; from distutils.version import LooseVersion; assert(LooseVersion($3) >= LooseVersion('$2'))" 2>/dev/null
	  else
   	     $PYTHON -c "import $1" 2>/dev/null
	  fi
	  if test $? -eq 0;
	  then
		AC_MSG_RESULT(yes)
  	  else
		AC_MSG_RESULT(no)
		if test "$4" = "required"; then
                  if test -n "$2"; then
		    AC_MSG_WARN(failed to find required module $1 with version >= $2)
		  else
		     AC_MSG_WARN(failed to find required module $1)
		  fi
		  PYTHON=""
		fi
	  fi
    fi	  
])

