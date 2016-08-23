# This is a short script for generating the top level wrapper code that
# initializes everything for cython. You don't normally run this directly,
# it is used by python.am for automatically creating this file.

import os
import sys
import re

tmpl_dir = os.path.dirname(sys.argv[0]) + "/"
cython_init_template = open(tmpl_dir + "cython_init.tmpl").read()
prototypes = []
initcmd = []
end_count = 0
for i in sys.argv[2:]:
    # Handle stuff we are including conditionally
    if(re.search('\AHAVE', i)):
        for c in range(end_count):
            prototypes.append("#endif")
            initcmd.append("#endif")
        end_count = 0
        for t in i.split():
            prototypes.append("#ifdef %s" % t)
            initcmd.append("#ifdef %s" % t)
            end_count += 1
    # Handle everything else
    else:
        prototypes.append("  CYTHON_INIT_TYPE CYTHON_INIT_FUNC(%s)(void);" % i)
        initcmd .append("  CYTHON_INIT_MODULE(cython_list, \"ecostress.%s\", CYTHON_INIT_FUNC(%s));" % (i, i))
# Make sure we close all the conditions
for c in range(end_count):
    prototypes.append("#endif")
    initcmd.append("#endif")
with open(sys.argv[1], 'w') as cython_init_fo:
    cython_init_fo.write(cython_init_template.format(prototypes="\n".join(prototypes),
                                                 initcmd="\n".join(initcmd)))


