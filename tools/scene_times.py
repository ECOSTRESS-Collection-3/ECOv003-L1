# Simple program to dump out orbit, scene, start time, end time for orbit
import h5py
import csv
import os
import glob
import re

fout = open("/home/smyth/scene_times.csv", "w")
w = csv.writer(fout)
w.writerow(['Orbit', 'SceneID', 'J2000 scene start time', 'J2000 scene end time'])
for topdir in glob.glob("/ops/store*/PRODUCTS/L1B_RAD"):
    for root, dirs, files in os.walk(topdir):
        for name in files:
            if(re.fullmatch(r'ECOSTRESS_L1B_RAD_.*_060[01]_01\.h5', name)):
                fname = os.path.join(root, name)
                print(fname)
                f = h5py.File(fname, "r")
                d = f["/Time/line_start_time_j2000"][:]
                # 1.18 is pretty close to the nominal_scan_time used by EcostressTimeTable
                w.writerow([int(f["/StandardMetadata/StartOrbitNumber"][()]),
                            int(f["/StandardMetadata/SceneID"][()]),
                            d[0], d[-1] + 1.18])
                f.close()
