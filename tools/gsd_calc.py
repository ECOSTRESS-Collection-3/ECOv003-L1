# Short script to calculate GSD for a particular scene. This is a one off, but
# We do things like this a lot, so it is worth leaving this as a template

from ecostress import *
from geocal import *
import sys
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
sns.set_theme()

l1_osp_dir="/home/smyth/Local/ecostress-test-data/latest/l1_osp_dir"
orbfname = "ECOv002_L1B_ATT_22352_20220615T152649_0700_01.h5"
radfname = "ECOv002_L1B_RAD_22352_010_20220615T162846_0700_02.h5"

igc = create_igc(radfname, orbfname, l1_osp_dir=l1_osp_dir)
gsd_line = []
gsd_sample = []
sample = []
for s in range(1,igc.number_sample-1, 1):
    gln, gsmp, _ = igc.gsd_values(ImageCoordinate(igc.number_line/2,s))
    gsd_line.append(gln)
    gsd_sample.append(gsmp)
    sample.append(s)

d = pd.DataFrame({"Sample" : sample,
                  "GSD Line" : gsd_line,
                  "GSD Sample" : gsd_sample})
sns.relplot(data=d,x="Sample",y="GSD Line", kind="scatter").set(title="GSD Line (m)")
plt.tight_layout()
plt.savefig("gsd_line.png", dpi=300)
sns.relplot(data=d,x="Sample",y="GSD Sample", kind="scatter").set(title="GSD Sample (m)")
plt.tight_layout()
plt.savefig("gsd_sample.png", dpi=300)

                        
