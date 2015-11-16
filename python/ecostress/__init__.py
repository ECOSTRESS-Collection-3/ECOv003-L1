# Just import any files we find in this directory, rather than listing
# everything

import os
import glob
import re
import imp

__path__.append(os.path.dirname(__file__) + "/../lib")

for i in glob.glob(os.path.dirname(__file__) + "/ecostress/*.py"):
    mname = os.path.basename(i).split('.')[0]
    # Don't load ipython, which is ipython magic extensions, or unit tests
    if(not mname == 'ipython' and
       not re.search('_test', mname)):
        exec "import %s" % mname
