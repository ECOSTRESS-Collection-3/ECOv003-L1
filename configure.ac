dnl Process this file with autoconf to produce a configure script.

AC_INIT(ecostress-level1, 0.01)
AC_CONFIG_AUX_DIR([config])
AC_CONFIG_MACRO_DIR([config/m4])
AC_CONFIG_FILES([script/setup_ecostress.csh script/setup_ecostress.sh])

ECOSTRESS_COMMON

AC_ARG_VAR([THIRDPARTY], [
It is common that you have a central location not already
searched for that you want to be searched for third party libraries. 
You can specify THIRDPARTY=<directory>. This gets added to all
the third party library checks.
])

#=================================================================
# Find python

AFIDS_PYTHON(required, cannot_build, default_search)

#=================================================================
# Location of all the source code directories
ECOSTRESS_SOURCE_DIRECTORY

AC_CONFIG_FILES([Makefile])
AC_OUTPUT

#======================================================================
# Give a nice log message describing what has been configured
#======================================================================

LOC_MSG()
LOC_MSG([ECOSTRESS Level 1 is now configured])
LOC_MSG()
LOC_MSG([  Installation directory:        ${prefix}])

