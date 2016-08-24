# Just import any files we find in this directory, rather than listing
# everything

import os
import glob

# Load cython stuff
import ecostress._ecostress_level1
for mname in ecostress._cython_module_list:
    exec("from %s import *" % mname)

for i in glob.glob(os.path.dirname(__file__) + "/*.py"):
    mname = os.path.basename(i).split('.')[0]
    # Don't load ipython, which is ipython magic extensions
    if(not mname == 'ipython'):
        exec("from .%s import *" % mname)

    

