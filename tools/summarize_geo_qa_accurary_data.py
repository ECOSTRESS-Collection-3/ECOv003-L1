import h5py
import os
import glob
import fnmatch
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Depends on summarize_geo_qa_data.py already having been run.

df = pd.read_pickle("summary_geo_qa_pandas.pkl")
# Filter out scenes with no matches
df_good = df[df['initial_accuracy'] > 0]
# Summarize data for each orbit
df = df_good.groupby(['orbnum'], as_index=False).median()

df.plot(x="orbnum", y="initial_accuracy", kind="scatter")
plt.xlabel("Orbit Number")
plt.ylabel("Geolocation Accuracy (m)")
plt.title("Initial Uncorrected Geolocation Accuracy (m)")
plt.savefig("initial.png", bbox_inches='tight', dpi=600)
df.plot(x="orbnum", y="final_accuracy", kind="scatter")
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


