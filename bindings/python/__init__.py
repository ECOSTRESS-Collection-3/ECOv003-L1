# Just import any files we find in this directory, rather than listing
# everything

from __future__ import absolute_import as _absolute_import
import os as _os
import glob as _glob

#import ecostress_swig._swig_wrap import *
import ecostress_swig._swig_wrap

for _i in _glob.glob(_os.path.dirname(__file__) + "/*.py"):
    exec('from .' + _os.path.basename(_i).split('.')[0] + ' import *')
del _i
del _os
del _glob
del _absolute_import

