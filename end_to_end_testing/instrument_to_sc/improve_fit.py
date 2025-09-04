#! /usr/bin/env python
#
# Work on improving the fit of an orbit
import geocal
from ecostress import *
import h5py
from pathlib import Path
from loguru import logger
import io
import os
import pandas as pd
import pickle

version = "1.0"
usage = """Usage:
  improve_fit.py [options] <orbit_num>
  improve_fit.py -h | --help
  improve_fit.py -v | --version

Work on improving the fit of an orbit

Options:
  -h --help         
       Print this message

  -v --version      
       Print program version
"""

def tpcol_scene(fh, ind, scene_list):
    tpcol = geocal.TiePointCollection()
    if "Tiepoints" not in fh[f"Tiepoint/Scene {scene_list[ind]}"]:
        return tpcol
    d = fh[f"Tiepoint/Scene {scene_list[ind]}/Tiepoints"][:,:]
    if len(d) < 80:
        return tpcol
    for i in range(d.shape[0]):
        tp = geocal.TiePoint(len(scene_list))
        tp.image_coordinate(ind, geocal.ImageCoordinate(d[i,0], d[i,1]))
        tp.is_gcp = True
        tp.ground_location = geocal.Ecr(d[i,2], d[i, 3], d[i, 4])
        tpcol.push_back(tp)
    return tpcol

def add_breakpoint(
        orb: geocal.OrbitOffsetCorrection,
        time_range_tp: list[tuple[geocal.Time, geocal.Time]],
        pass_number: int,
) -> None:
    tlast = None
    for tmin, tmax in time_range_tp:
        if False and tlast is None and pass_number == 1:
            orb.insert_position_time_point(tmin)
        if tlast is None or tmin - tlast > 52.0:
            orb.insert_attitude_time_point(tmin)
        orb.insert_attitude_time_point(tmin + (tmax - tmin) / 2)
        orb.insert_attitude_time_point(tmax)
        tlast = tmax
    if False and tlast is not None and pass_number == 1:
        orb.insert_position_time_point(tlast)

def add_breakpoint2(
        orb: geocal.OrbitOffsetCorrection,
        time_range_tp: list[tuple[geocal.Time, geocal.Time]],
        pass_number: int,
) -> None:
    tlast = None
    tmink = None
    for tmin, tmax in time_range_tp:
        if tlast is None and pass_number == 1:
            orb.insert_attitude_time_point(tmin)
            tmink = tmin 
        #if tlast is None or tmin - tlast > 52.0:
        #    orb.insert_attitude_time_point(tmin)
        #orb.insert_attitude_time_point(tmin + (tmax - tmin) / 2)
        #orb.insert_attitude_time_point(tmax)
        tlast = tmax
    if tlast is not None and pass_number == 1:
        orb.insert_attitude_time_point(tlast)
        #orb.insert_attitude_time_point(tmin+ (tlast - tmin)/2)

def accuracy_result(igccol_initial, igccol, tpcol):
    data = []
    for i in range(igccol.number_image):
        dfinit = tpcol.data_frame(igccol_initial, i)
        ackinit = dfinit.ground_2d_distance.quantile(0.68)
        df = tpcol.data_frame(igccol, i)
        ack = df.ground_2d_distance.quantile(0.68)
        ntp = np.count_nonzero(np.isnan(df["line"]) == False)
        logger.info(f"{igccol.title(i)} - {ack} m from {ntp} tiepoints Initial {ackinit} m")
        data.append([args.orbit_num, scene_list[i], ackinit, ack, ntp])
    data = np.array(data)
    df = pd.DataFrame({"orbnum" : data[:,0].astype(int),
                       "scene" : data[:,1].astype(int),
                       "initial_accuracy" : data[:,2],
                       "final_accuracy" : data[:, 3],
                       "number_tiepoint" : data[:, 4]
                       })
    df.to_pickle("accuracy.pkl")

args = geocal.docopt_simple(usage, version=version)
qa_path = Path("/arcdata/smyth/L1B_GEO_QA/2025/04")
l1a_raw_att_path = Path("/arcdata/smyth/L1A_RAW_ATT/2025/04")
l1b_rad_path = Path("/arcdata/smyth/L1B_RAD/2025/04")
qa_fh = h5py.File(next(qa_path.glob(f"*/*_{args.orbit_num}_*.h5")))
scene_list = [int(t[6:]) for t in qa_fh["Accuracy Estimate/Scenes"][:]]

l1a_raw_att= next(l1a_raw_att_path.glob(f"*/*_{args.orbit_num}_*.h5"))
l1b_rad = [next(l1b_rad_path.glob(f"*/*_{args.orbit_num}_{scn:03d}_*.h5")) for scn in scene_list]
l1bgeo = L1bGeoProcess(prod_dir=Path(f"./orbit_{args.orbit_num}"),
                       l1a_raw_att=l1a_raw_att,
                       l1_osp_dir=Path("./l1_osp_dir"),
                       l1b_rad=l1b_rad,)

geocal.makedirs_p(str(l1bgeo.prod_dir))
os.chdir(l1bgeo.prod_dir)
logger.add(l1bgeo.prod_dir / "result.log", level="DEBUG")
# May want to include this somehow, so we derive from L1bGeoProcess or something.
# But we don't know enough yet to do this intelligently, so just do this inline
logger.add(l1bgeo.log_file, level="DEBUG")
l1bgeo.log_string_handle = io.StringIO()
logger.add(l1bgeo.log_string_handle, level="DEBUG")
with open("extra_python_init.py", "w") as fh:
    print("from ecostress import *\n", file=fh)
l1bgeo.radlist = l1bgeo.filter_scene_failure(l1bgeo.radlist)
l1bgeo.determine_output_file_name()
igccol_initial = l1bgeo.create_igccol_initial()
trange = []
for i in range(igccol_initial.number_image):
    trange.append([igccol_initial.image_ground_connection(i).time_table.min_time,
                   igccol_initial.image_ground_connection(i).time_table.max_time])
tpcol = geocal.TiePointCollection()
tmlist = []
for i in range(igccol_initial.number_image):
    tpd = tpcol_scene(qa_fh, i, scene_list)
    if(len(tpd) > 0):
        tpcol.extend(tpd)
        tmlist.append(trange[i])
if(len(tpcol) > 0):
    add_breakpoint2(l1bgeo.orb, tmlist, 1)
    igccol_corrected = l1bgeo.run_sba(igccol_initial, tpcol, 1)
    logger.info(igccol_corrected)
    accuracy_result(igccol_initial, igccol_corrected, tpcol)
    pickle.dump(np.reshape(igccol_corrected.parameter_subset, [-1,3]), open("quat.pkl", "wb"))
    # df = pd.read_pickle("accuracy.pkl")
    # quat_ypr = pickle.load(open("quat.pkl", "rb")
else:
    logger.info("No scenes have sufficient number of tiepoints")
