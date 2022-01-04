#! /usr/bin/env python
#
# Fit/plot overlap between scan lines

import geocal
import ecostress
import pandas as pd
import matplotlib.pyplot as plt
import scipy
import pickle

version = "1.0"
usage='''Usage:
  fit_overlap.py [options] <orbit_num> <scene>
  fit_overlap.py -h | --help
  fit_overlap.py -v | --version

This fits/plots the overlap between scan lines

Options:
  -h --help         
       Print this message

  --fit
       Fit parameters

  --parameter-file=f
       Parameter file to update parameter to.

  -v --version      
       Print program version
'''

def residual(x, igccol, mpts):
    igccol.parameter_subset = x
    igc = igccol.image_ground_connection(0)
    res = []
    for i, ic1, _, mic in mpts:
        ic2, success = igc.image_coordinate_scan_index(igc.ground_coordinate(ic1), i+1)
        if(success):
            res.append(ic2.line - mic.line)
            res.append(ic2.sample - mic.sample)
    return res

args = geocal.docopt_simple(usage, version=version)
igccol = ecostress.create_igccol(args.orbit_num, args.scene,
                   title=f"Orbit {args.orbit_num} Scene {args.scene}")
igc = igccol.image_ground_connection(0)
mpts = igc.match_all_overlap()
data = []
for scan, ic1, ic2, ic2_match in mpts:
    data.append([ic1.line, ic1.sample, ic2_match.line - ic2.line,
                 ic2_match.sample - ic2.sample])
df_original = pd.DataFrame(data,
                  columns = ["line", "sample", "line_diff", "sample_diff"])

parameter_update = None
if(args.fit):
    # Not sure about set here to fit for. We'll probably need to play
    # with this
    igc.camera.mask_all_parameter()
    igc.scan_mirror.fit_second_angle_per_encoder_value = True
    igc.scan_mirror.fit_second_encoder_value_at_0 = True
    igc.scan_mirror.fit_camera_to_mirror_yaw = True
    igc.scan_mirror.fit_camera_to_mirror_2_yaw = True
    igc.scan_mirror.fit_camera_to_mirror_pitch = True
    igc.scan_mirror.fit_camera_to_mirror_2_pitch = True
    igc.scan_mirror.fit_camera_to_mirror_roll = True
    igc.scan_mirror.fit_camera_to_mirror_2_roll = True
    igc.camera.fit_focal_length = True
    igc.camera.fit_principal_point_line(True, 1)
    igc.camera.fit_principal_point_sample(True, 1)
    x0 = igccol.parameter_subset
    print("Initial values")
    for i in range(len(igccol.parameter_subset)):
        print("  ", igccol.parameter_name_subset[i], ": ",
              igccol.parameter_subset[i])
    r = scipy.optimize.least_squares(residual, x0, args=(igccol,mpts))
    print(r)
    print("Fitted values")
    for i in range(len(igccol.parameter_subset)):
        print("  ", igccol.parameter_name_subset[i], ": ",
              igccol.parameter_subset[i])
    pickle.dump(igccol.parameter, open("%05d_%03d_parameter_fit.pkl" %
                                       (int(args.orbit_num), int(args.scene)),
                                       "wb"))
    parameter_update = igccol.parameter
if(args.parameter_file):
    parameter_update = pickle.load(open(args.parameter_file, "rb"))

df_update = None
if(parameter_update is not None):
    igccol.parameter = parameter_update
    data = []
    for i, ic1, _, mic in mpts:
        ic2, success = igc.image_coordinate_scan_index(igc.ground_coordinate(ic1), i+1)
        if(success):
            data.append([ic1.line, ic1.sample, ic2.line - mic.line,
                         ic2.sample - mic.sample])
    df_update = pd.DataFrame(data,
                 columns = ["line", "sample", "line_diff", "sample_diff"])
    

df_original.plot(x="sample", y="sample_diff", kind="scatter")
plt.xlabel("Sample")
plt.ylabel("Sample Diff")
plt.title(f"{igc.title} overlap sample diff")
plt.savefig("%05d_%03d_sample_diff.png" %
            (int(args.orbit_num), int(args.scene)),
            bbox_inches='tight', dpi=300)
df_original.plot(x="sample", y="line_diff", kind="scatter")
plt.xlabel("Sample")
plt.ylabel("Line Diff")
plt.title(f"{igc.title} overlap line diff")
plt.savefig("%05d_%03d_line_diff.png" %
            (int(args.orbit_num), int(args.scene)),
            bbox_inches='tight', dpi=300)
print(df_original["sample_diff"].describe())
print(df_original["line_diff"].describe())
if(df_update is not None):
    print(df_update["sample_diff"].describe())
    print(df_update["line_diff"].describe())
