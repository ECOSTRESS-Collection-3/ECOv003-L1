# Source directory for ECOSTRESS

AC_DEFUN([ECOSTRESS_SOURCE_DIRECTORY], [
AC_SUBST([l1a_raw_src], [l1a_raw])
AC_SUBST([l1a_cal_src], [l1a_cal])
AC_SUBST([l1b_rad_src], [l1b_rad])
AC_SUBST([l1b_geo_src], [l1b_geo])
AC_SUBST([srcscript], [script])
AC_SUBST([srcpython], [python])
AC_SUBST([srcpythonlib], [${srcpython}/lib])
AC_SUBST([srccython], [bindings/python/cython])
AC_SUBST([pythonsrccython], [bindings/python])
AC_SUBST([installecostressdir], [\${prefix}])
AC_SUBST([ecostresspkgpythondir],[\${prefix}/${pythondir}/ecostress])
])

