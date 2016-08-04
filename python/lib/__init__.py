# Just import any files we find in this directory, rather than listing
# everything

from __future__ import absolute_import
import os
import re
import glob
from geocal import *

for i in glob.glob(os.path.dirname(__file__) + "/*.py"):
    mname = os.path.basename(i).split('.')[0]
    # Don't load ipython, which is ipython magic extensions, or unit tests
    if(not mname == 'ipython' and
       not re.search('_test', mname)):
        exec("from .%s import *" % mname)
