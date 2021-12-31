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
orb_initial_accuracy = {}
orb_final_accuracy = {}
# Split this up, just in case we want to update pandas w/o reading all
# the data again
if(not os.path.exists("accuracy.p")):
    for orb, fname in orb_to_file.items():
        print("Doing ", orb)
        f = h5py.File(fname)
        orb_initial_accuracy[orb] = f["/Accuracy Estimate/Accuracy Before Correction"][:]
        orb_final_accuracy[orb] = f["/Accuracy Estimate/Final Accuracy"][:]
    pickle.dump([orb_initial_accuracy, orb_final_accuracy],
                open( "accuracy.p", "wb" ))
if(not os.path.exists("accuracy_pandas.pkl")):
    orb_initial_accuracy, orb_final_accuracy = pickle.load( open( "accuracy.p", "rb" ))
    data = []
    for (orb, iacc) in orb_initial_accuracy.items():
        t = iacc[iacc > 0]
        t2 = orb_final_accuracy[orb][iacc > 0]
        if(len(t) > 0):
            data.append([int(orb), np.median(t), t.min(), t.max(),
                         np.median(t2), t2.min(), t2.max()])
    df = pd.DataFrame(data, columns = ["orb",
                                       "initial_accuracy",
                                       "initial_accuracy_min",
                                       "initial_accuracy_max",
                                       "final_accuracy",
                                       "final_accuracy_min",
                                       "final_accuracy_max"])
    df.to_pickle("accuracy_pandas.pkl")
df = pd.read_pickle("accuracy_pandas.pkl")
df.plot(x="orb", y="initial_accuracy", kind="scatter")
plt.xlabel("Orbit Number")
plt.ylabel("Geolocation Accuracy (m)")
plt.title("Initial Uncorrected Geolocation Accuracy (m)")
plt.savefig("initial.png", bbox_inches='tight', dpi=600)
df.plot(x="orb", y="final_accuracy", kind="scatter")
plt.ylim(0,100)
plt.xlabel("Orbit Number")
plt.ylabel("Geolocation Accuracy (m)")
plt.title("Final Corrected Geolocation Accuracy")
plt.savefig("final.png", bbox_inches='tight', dpi=600)
pd.DataFrame.hist(df, column="final_accuracy", range=(0,100))
plt.xlabel("Geolocation Accuracy (m)")
plt.title("Final Corrected Geolocation Accuracy")
plt.savefig("final_hist.png", bbox_inches='tight', dpi=600)
pd.DataFrame.hist(df, column="initial_accuracy", range=(0,4000))
plt.xlabel("Geolocation Accuracy (m)")
plt.title("Initial Uncorrected Geolocation Accuracy (m)")
plt.savefig("initial_hist.png", bbox_inches='tight', dpi=600)
print(df["final_accuracy"].describe())
print(df["initial_accuracy"].describe())


