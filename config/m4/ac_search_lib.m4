# SYNOPSIS
#
#   AC_SEARCH_LIB([BASE], [pkgcfg name], [header_path], [header], 
#                 [lib_path], [lib], [link])
#
# DESCRIPTION
# This searchs for a library. We do this by first looking looking for a
# pkgcfg file, and then by searching for a given header and library.
# If found, we set BASE_CFLAGS, BASE_LIBS, and BASE_PREFIX (useful to pass
# down to other thirdparty library builds.

AC_DEFUN([AC_SEARCH_LIB],
[
  PKG_CHECK_MODULES([$1], [$2], [succeeded=yes], [succeeded=no])
  if test "$succeeded" = "yes"; then
     if test -z "$[$1][_PREFIX]"; then
        [$1][_PREFIX]=`$PKG_CONFIG --variable=prefix "$2" 2>/dev/null`
     fi
  fi
  if test "$succeeded" = "no"; then
     for ac_path_tmp in $prefix $CONDA_PREFIX $THIRDPARTY /opt/afids_support /opt/afids /usr /usr/local /opt /opt/local /opt/local/lib/hdfeos5 /sw ; do
       if test -e "$ac_path_tmp/include/$3$4" && test -r "$ac_path_tmp/include/$3$4"; then
          [$1][_PREFIX]=$ac_path_tmp
          [$1][_CFLAGS]="-I$ac_path_tmp/include/$3"
          if test -e "$ac_path_tmp/lib/$5$6.so"; then
             [$1][_LIBS]="-R$ac_path_tmp/lib/$5 -L$ac_path_tmp/lib/$5 $7"
             succeeded=yes
             break;
          elif test -e "$ac_path_tmp/lib/$5$6.dylib"; then
             [$1][_LIBS]="-R$ac_path_tmp/lib/$5 -L$ac_path_tmp/lib/$5 $7"
             succeeded=yes
             break;
          elif test -e "$ac_path_tmp/lib64/$5$6.so"; then
             [$1][_LIBS]="-R$ac_path_tmp/lib64/$5 -L$ac_path_tmp/lib64/$5 $7"
             succeeded=yes
             break;
          elif test -e "$ac_path_tmp/lib64/$5$6.dylib"; then
             [$1][_LIBS]="-R$ac_path_tmp/lib64/$5 -L$ac_path_tmp/lib64/$5 $7"
             succeeded=yes
             break;
          fi
       fi
     done
  fi
])

