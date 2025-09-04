# Combine the results from all the runs
import pandas as pd
from pathlib import Path
import numpy as np
import pickle

pdpath = Path(".")
dfall = pd.concat([pd.read_pickle(f) for f in pdpath.glob("orbit_*/accuracy.pkl")])
dfall.to_pickle("accuracy_all.pkl")

quatall = np.concatenate([pickle.load(open(f, "rb")) for f in pdpath.glob("orbit_*/quat.pkl")])
pickle.dump(quatall, open("quatall.pkl", "wb"))
print(dfall[dfall['number_tiepoint'] > 0].describe(percentiles=[0.25,0.5,0.68,0.90, 0.95]))
print(np.average(quatall, axis=0))
