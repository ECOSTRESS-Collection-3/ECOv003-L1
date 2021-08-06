# SYNOPSIS
#
#   AC_HANDLE_WIITH_ARG([variable name], ["with" name"], [Description name], 
#                       [can_build], [default_build], [do_not_use])
#
# DESCRIPTION
#
# This process the "--with-blah-blah" argument. This processes the argument,
# sets up the help message, and determines the logic for if we 
# want, and are going to build a particular item. For a variable name
# "blah_blah", this would set up the variables want_blah_blah, 
# build_blah_blah, build_needed_blah_blah and ac_blah_blah_path.
#
# Note that the "variable name" and "with name" are generally pretty similar.
# The difference is that "with" names typically contain "-" in the (e.g.,
# "with-vicar-rtl"), while the variable names can't have this in it (so
# the variable name would be "vicar_rtl").
#
# A particular package might not have the library source code, so you
# can supply the "can_build" argument as "can_build". Empty string means we
# can't build this, and various help messages etc. are adjusted for this.
#
# If the user doesn't otherwise specify the "with" argument for this
# library, we can either have a default behavior of searching for the
# library on the system or of building our own copy of it. You can
# specify "default_build" if this should build, otherwise we just look
# for this on the system.

AC_DEFUN([AC_HANDLE_WITH_ARG],[
[have_][$1]="no"
[build_][$1]="no"
[build_needed][$1]="no"
[want_][$1]="no"
if test "$6" != "do_not_use"; then
  AC_ARG_WITH([$2],
        AS_HELP_STRING([--with-][$2][@<:@=DIR@:>@], [use ][$3][ (default is yes if found) - it is possible to specify the root directory for ][$3][ (optional).]m4_bmatch([$4],[can_build], [ You can also specify "build" if you want to build your own local copy. See also THIRDPARTY variable described below.])),
        [
    if test "$withval" = "no"; then
        [want_][$1]="no"
    elif test "$withval" = "yes"; then
        [want_][$1]="yes"
        [ac_][$1][_path]=""
    elif test "$withval" = "build"; then
        if test "$4" != "can_build"; then
            AC_MSG_ERROR([The "build" option is not supported in this particular package for --with-][$2])
        fi
        [want_][$1]="yes"
        [build_][$1]="yes"
        [ac_][$1][_path]="\${prefix}"
    else
        [want_][$1]="yes"
        [ac_][$1][_path]="$withval"
    fi
    ],
    [
    [want_][$1]="yes"
    if test "$4" = "can_build"; then
      if test "$5" = "default_build" -o "$THIRDPARTY" = "build"; then
        [want_][$1]="yes"
        [build_][$1]="yes"
        [ac_][$1][_path]="\${prefix}"
      elif test "$THIRDPARTY" = "build_needed"; then
        [want_][$1]="yes"
        [build_needed_][$1]="yes"
      fi
    fi
    ])
fi
])

# Variation where if the user doesn't give anything we default to no
AC_DEFUN([AC_HANDLE_WITH_ARG_DEFAULT_NO],[
[have_][$1]="no"
[build_][$1]="no"
[build_needed][$1]="no"
[want_][$1]="no"
if test "$6" != "do_not_use"; then
  AC_ARG_WITH([$2],
        AS_HELP_STRING([--with-][$2][@<:@=DIR@:>@], [use ][$3][ (default is no) - it is possible to specify the root directory for ][$3][ (optional).]m4_bmatch([$4],[can_build], [ You can also specify "build" if you want to build your own local copy. See also THIRDPARTY variable described below.])),
        [
    if test "$withval" = "no"; then
        [want_][$1]="no"
    elif test "$withval" = "yes"; then
        [want_][$1]="yes"
        [ac_][$1][_path]=""
    elif test "$withval" = "build"; then
        if test "$4" != "can_build"; then
            AC_MSG_ERROR([The "build" option is not supported in this particular package for --with-][$2])
        fi
        [want_][$1]="yes"
        [build_][$1]="yes"
        [ac_][$1][_path]="\${prefix}"
    else
        [want_][$1]="yes"
        [ac_][$1][_path]="$withval"
    fi
    ],
    [
    [want_][$1]="no"])
fi
])
