#! /usr/bin/env python
#
# Script to find the mapping from orbit to start date, used to
# find files on the system

import h5py
import os
import glob
import fnmatch
import pickle

orb_to_date = {}
for i in glob.glob("/ops/store*/PRODUCTS/L1A_RAW_ATT"):
    for(dirpath, dirname, files) in os.walk(i):
        for f in files:
            if fnmatch.fnmatch(f, 'L1A_RAW_ATT_*.h5'):
                fh = h5py.File(os.path.join(dirpath, f))
                dt1 = fh["/StandardMetadata/RangeBeginningDate"][()]
                dt1 = dt1.decode('utf-8').replace("-", "/")
                dt2 = fh["/StandardMetadata/RangeEndingDate"][()]
                dt2 = dt2.decode('utf-8').replace("-", "/")
                orb = int(fh["/StandardMetadata/StartOrbitNumber"][()])
                print(f"Doing orbit {orb}")
                orb_to_date[orb] = [dt1, dt2]
pickle.dump(orb_to_date, open("/project/sandbox/smyth/orbit_to_date.pkl", "wb"))
