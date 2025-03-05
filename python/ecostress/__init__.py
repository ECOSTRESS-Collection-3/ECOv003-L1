# Just import any files we find in this directory, rather than listing
# everything.

from __future__ import absolute_import
import os as _os
import re as _re
import glob as _glob
from .version import __version__
from ecostress_swig import * # type: ignore

for _i in _glob.glob(_os.path.dirname(__file__) + "/*.py"):
    mname = _os.path.basename(_i).split('.')[0]
    # Don't load ipython, which is ipython magic extensions, or unit tests
    if not mname == "ipython" and not _re.search("_test", mname):
        exec("from .%s import *" % mname)
del _i
del _re
del _os
del _glob
