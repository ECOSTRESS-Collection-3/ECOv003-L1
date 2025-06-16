# Source directory for ECOSTRESS

AC_DEFUN([ECOSTRESS_SOURCE_DIRECTORY], [
AC_SUBST([l1a_raw_src], [l1a_raw])
AC_SUBST([l1a_cal_src], [l1a_cal])
AC_SUBST([l1b_rad_src], [l1b_rad])
AC_SUBST([l1b_geo_src], [l1b_geo])
AC_SUBST([l1c_src], [l1c])
AC_SUBST([srcscript], [script])
AC_SUBST([srcpython], [python])
AC_SUBST([srcpdf], [vicar_pdf])
AC_SUBST([srclib], [lib])
AC_SUBST([srcpythonlib], [${srcpython}/lib])
AC_SUBST([testsupportsrc], [${srcpython}/test_support])
AC_SUBST([srccython], [bindings/python/cython])
AC_SUBST([pythonsrccython], [bindings/python])
AC_SUBST([pythonswigsrc], [bindings/python])
AC_SUBST([swigsrc], [bindings/python/swig])
AC_SUBST([installecostressdir], [\${prefix}])
AC_SUBST([vicarpdfdir], [\${prefix}/vicar_pdf])
AC_SUBST([ecostresspkgpythondir],[\${prefix}/${pythondir}/ecostress])
AC_SUBST([unittestdata], [unit_test_data])
])

