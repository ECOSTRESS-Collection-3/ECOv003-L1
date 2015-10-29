# SYNOPSIS
#
#   AC_CHECK_FOUND([variable name], ["with" name], [library name], [required], 
#                  [can_build])
#
# DESCRIPTION
#
# Check if the library was found, if if not then print out an
# error message.
#
# A particular package might not have the library source code, so you
# can supply the "can_build" argument as "can_build". Empty string means we
# can't build this, and various help messages etc. are adjusted for this.
#
# Not finding this library might or might not indicate an error. If you
# want an error to occur if we don't find the library, then specify
# "required". Otherwise, leave it as empty and we'll just silently
# return if we don't find the library.

AC_DEFUN([AC_CHECK_FOUND],
[
if test "$4" = "required"; then
  if test "[$have_][$1]" = "no"; then
     AC_MSG_ERROR([
The ][$3][ library is required by GeoCal. Try specifying
location using --with-][$2][ if configure could't find the
library.] m4_bmatch([$5],[can_build], [You can specify --with-][$2][=build if you want to build your
own local copy of ][$3][.

You can also specify THIRDPARTY=build if you want to build a local
copy of all the libraries/programs.
]))
  fi
fi
])
