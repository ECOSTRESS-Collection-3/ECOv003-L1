AC_DEFUN([AC_ENABLE_DEBUG],[

AC_MSG_CHECKING([whether to enable debug flags when compiling])
AC_ARG_ENABLE(debug,
AS_HELP_STRING([--enable-debug],[Enable compiler debugging flags]),
[if test "$enableval" = yes; then
  AC_MSG_RESULT([yes])
  if test "$GCC" = yes; then
    CXXFLAGS="-ggdb -DBZ_DEBUG -fbounds-check"
    CFLAGS="-ggdb -fbounds-check"
# There are some legitimate uses of mve in p1 that appear to violate the
# bounds-check. This is because arrays are passed into fortran that have
# negative indicies, which is allowed in fortran. So turn off the bound-check
# for fortran.
    FFLAGS="-ggdb"
  fi
fi],
[AC_MSG_RESULT([no])
 enable_debug=no
 AC_DEFINE([BOOST_DISABLE_ASSERTS],[],[Disable assertions in boost])
 CXXFLAGS="$CXXFLAGS -Wall"
 CFLAGS="$CFLAGS -Wall"
]
)
AC_ARG_VAR([DEBUG_FLAGS],[Compiler debugging flags])
])

