# Just import any files we find in this directory, rather than listing
# everything

import os as _os
import glob as _glob

from ecostress_swig import *

# Load cython stuff
import ecostress._ecostress_level1
for _mname in ecostress._cython_module_list:
    exec("from %s import *" % _mname)

for _i in _glob.glob(_os.path.dirname(__file__) + "/*.py"):
    _mname = _os.path.basename(_i).split('.')[0]
    # Don't load ipython, which is ipython magic extensions
    if(not _mname == 'ipython'):
        exec("from .%s import *" % _mname)

del _i
del _mname
del _os
del _glob

    

