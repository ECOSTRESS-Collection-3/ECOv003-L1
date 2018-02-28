# Just import any files we find in this directory, rather than listing
# everything.

# ***** Note
# This init is just used for local testing. In particular, it doesn't load the
# cython stuff. There is another __init__ file found at ../init/__init__.py that
# is used for the full installed library. The purpose of this init it to
# be able to locally run tests and do development without installing the full
# system.

import os as _os
import re as _re
import glob as _glob
from ecostress_swig import *

for _i in _glob.glob(_os.path.dirname(__file__) + "/*.py"):
    mname = _os.path.basename(_i).split('.')[0]
    # Don't load ipython, which is ipython magic extensions, or unit tests
    if(not mname == "ipython" and
       not mname == "cython_try" and
       not _re.search('_test', mname)):
        exec("from .%s import *" % mname)
del _i
del _re
del _os
del _glob
