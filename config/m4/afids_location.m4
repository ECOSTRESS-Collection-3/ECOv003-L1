# Have defaults for location of afids and geocal, but let the user override
# these

AC_DEFUN([AFIDS_LOCATION],
[
AC_ARG_WITH([afids],
AS_HELP_STRING([--with-afids=DIR], [give directory where afids can be found (optional, default is /pkg/afids/afids_latest)]), [ ac_afids_dir="$withval" ], [ ac_afids_dir="/pkg/afids/afids_latest" ])
AC_SUBST([afidsdir], ["$ac_afids_dir"])

AC_ARG_WITH([geocal],
AS_HELP_STRING([--with-geocal=DIR], [give directory where geocal can be found (optional, default is /pkg/afids/geocal_latest)]), [ ac_geocal_dir="$withval" ], [ ac_geocal_dir="/pkg/afids/geocal_latest" ])
AC_SUBST([geocaldir], ["$ac_geocal_dir"])
PKG_CONFIG_PATH=$ac_geocal_dir/lib/pkgconfig:$PKG_CONFIG_PATH
PKG_CHECK_MODULES([GEOCAL], [geocal])
PKG_CHECK_VAR([GEOCAL_SWIG_CFLAGS], [geocal], [swig_cflags])

AC_ARG_WITH([test-data],
AS_HELP_STRING([--with-test-data=DIR], [give directory where end to end test data can be found (optional, default is /project/test/ASTER/EndToEndTest)]), [ ac_test_data_dir="$withval" ], [ ac_test_data_dir="/project/test/ASTER/EndToEndTest" ])
AC_SUBST([testdatadir], ["$ac_test_data_dir"])

])
