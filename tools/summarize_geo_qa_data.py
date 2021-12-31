# Similar to summarize, but summarize more data. We'll leave the original in
# place which focused on accuracy, but this collects more information
import h5py
import os
import glob
import fnmatch
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# We might see the same orbit multiple times. In that case, select
# the latest version. For multiple version maps, pick the latest version.
orb_to_ver = {}
orb_to_file = {}
for i in glob.glob("/ops/store*/PRODUCTS/L1B_GEO_QA"):
    for(dirpath, dirname, files) in os.walk(i):
        for f in files:
            if fnmatch.fnmatch(f, 'L1B_GEO_QA_*.h5'):
                _,_,_,orb,_,ver,pnum = f.split("_")
                ver = "%s_%s" % (ver, pnum)
                if(orb in orb_to_ver and
                   ver < orb_to_ver[orb]):
                    pass
                else:
                    orb_to_file[orb] = os.path.join(dirpath, f)
                    orb_to_ver[orb] = ver
orb_data = {}
data = None
for orb, fname in orb_to_file.items():
    print("Doing ", orb)
    try:
        f = h5py.File(fname)
        # We save all this in a double array just for convenience,
        # even though some of the data is actually integer. The
        # columns in order are orbit, scene number, accuracy
        # before correction, final accuracy, solar zenith, land
        # fraction, initial number tiepoint, blunders removed,
        # final number tiepoint
        t = f["/Accuracy Estimate/Accuracy Before Correction"][:]
        d = np.empty((len(t), 9))
        d[:,0] = int(orb)
        d[:,1] = [int(f["Accuracy Estimate/Scenes"][i][6:])
                  for i in range(d.shape[0])]
        d[:,2] = t
        d[:,3] = f["/Accuracy Estimate/Final Accuracy"][:]
        d[:,4:6] = f["/Average Metadata"]
        d[:,6:] = f["/Tiepoint/Tiepoint Count"]
        orb_data[orb] = d
        if(data is None):
            data = d
        else:
            data = np.concatenate((data,d),axis=0)
    except KeyError:
        print("Orbit failed, skipping")
df = pd.DataFrame(data, columns = ["orbnum",
                                   "scene",
                                   "initial_accuracy",
                                   "final_accuracy",
                                   "solar_zenith",
                                   "land_fraction",
                                   "initial_tiepoint",
                                   "blunder_removed",
                                   "final_tiepoint"])
df.to_pickle("summary_pandas.pkl")
# Can get a set with good tiepoints by:
# import pandas as pd
# import pandasql as pds
# df = pd.read_pickle("summary_pandas.pkl")
# t = pds.PandaSQL(persist=True)
# t("select * from df where final_tiepoint = 326")


