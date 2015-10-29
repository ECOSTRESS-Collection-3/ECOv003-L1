# SYNOPSIS
#
#   AC_PYTHON_MODULE_WITH_VERSION(modname, required_version, module version)
#
# Variation of AC_PYTHON_MODULE that also tests the version of a module.
#serial 6

AC_DEFUN([AC_PYTHON_MODULE_WITH_VERSION],[
    if test -z $PYTHON;
    then
        PYTHON="python"
    fi
    PYTHON_NAME=`basename $PYTHON`
    AC_MSG_CHECKING($PYTHON_NAME module: $1)
	$PYTHON -c "import $1; from distutils.version import LooseVersion; assert(LooseVersion($3) >= LooseVersion('$2'))" 2>/dev/null
	if test $? -eq 0;
	then
		AC_MSG_RESULT(yes)
	else
		AC_MSG_RESULT(no)
		AC_MSG_ERROR(failed to find required module $1 with version >= $2)
		exit 1
	fi
])
