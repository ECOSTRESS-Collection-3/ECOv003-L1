dnl Process this file with autoconf to produce a configure script.

AC_INIT(ecostress-level1, 0.20)
AC_CONFIG_AUX_DIR([config])
AC_CONFIG_MACRO_DIR([config/m4])
AC_CONFIG_FILES([script/setup_ecostress.csh script/setup_ecostress.sh])

ECOSTRESS_COMMON

#=================================================================
# Find location of afids and geocal

AFIDS_LOCATION

#=================================================================
# Find h5diff
AC_PATH_PROG([H5DIFF], [h5diff], "", [$PATH$PATH_SEPARATOR${ac_afids_dir}/bin])
if test -z "$H5DIFF"; then
   AC_MSG_ERROR([Cannot find h5diff])
fi

#=================================================================
# Find python. Note that the virtual environment has modules that
# depend on the afids build, so set LD_LIBRARY_PATH here for AFIDS
# before checking all the modules.

original_ld_library_path="${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH="${afidsdir}/lib64:${afidsdir}/lib:${LD_LIBRARY_PATH}"
AFIDS_PYTHON(required, cannot_build, default_search)
LD_LIBRARY_PATH="${original_ld_library_path}"

#=================================================================
# Location of all the source code directories
ECOSTRESS_SOURCE_DIRECTORY

#=================================================================
# Use cython
AC_PROG_CYTHON()

if test "$have_cython" = "yes" -a "$USE_MAINTAINER_MODE" != "no"; then
  generate_cython="yes"
else
  generate_cython="no" 
fi

AC_CONFIG_FILES([Makefile])
AC_OUTPUT

#======================================================================
# Give a nice log message describing what has been configured
#======================================================================

LOC_MSG()
LOC_MSG([ECOSTRESS Level 1 is now configured])
LOC_MSG()
LOC_MSG([  Installation directory:        ${prefix}])
LOC_MSG([  Build debug version:           ${enable_debug}])
LOC_MSG([  CXX compiler:                  ${CXX} ${CXXFLAGS}])
LOC_MSG()
LOC_MSG([  Generate cython wrappers:      ${generate_cython}])

