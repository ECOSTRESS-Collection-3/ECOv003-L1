# This creates test data end to end.
from geocal import *
from ecostress import *
import h5py
from multiprocessing import Pool

# Center times for each of the passes. See the wiki at 
# https://wiki.jpl.nasa.gov/display/ecostress/Test+Data and subpages for details

pass_time = [Time.parse_time("2015-01-14T12:00:24.995464Z"),
            Time.parse_time("2015-03-11T13:27:08.758614Z"),
            Time.parse_time("2015-03-02T16:34:33.146760Z"),
            Time.parse_time("2015-04-16T22:13:14.347679Z"),
            Time.parse_time("2015-01-24T14:43:18.819553Z")]
orbit_num = [80001, 80002, 80003, 80004, 80005]
nscene = [1,1,1,1,3]

pass_index = 4 # The pass we are working with

# Get the ASTER mosaic we are working with for all the bands. The
# bands comes from the wiki. Data originally comes from /raid11/astermos,
# but is compressed there.
# (data is only on pistol
def fname(band):
    return "/data/smyth/AsterMosiac/calnorm_b%d.img" % band
# These scale factors comes from https://lpdaac.usgs.gov/dataset_discovery/aster/aster_products_table/ast_l1t
scale_factor = [1.688, 1.415, 0.862, 0.2174, 0.0696, 0.0625, 0.0597, 0.0417, 0.0318,
                6.882e-3, 6.780e-3, 6.590e-3, 5.693e-3, 5.225e-3]
sdata = [ScaleImage(VicarLiteRasterImage(fname(aster_band), 1, VicarLiteFile.READ,
                                         5000, 5000),
                    scale_factor[aster_band-1])
         for aster_band in [14, 14, 12, 11, 10, 4]]

orb = SpiceOrbit(SpiceOrbit.ISS_ID, "iss_spice/iss_2015.bsp")

# Focal length and ccd pixel size comes from Eugene's SDS data
# bible. The scaling of the CCD size is empirical to give the right
# resolution on the surface. These are pretty hoaky, we really just
# want something vaguely right since our camera model is pretty
# different from a pushbroom. But this gives a place to start.

frame_to_sc = quat_rot("ZYX", 0, 0, 0)
cam = QuaternionCamera(frame_to_sc, 1, 5400, 40e-3 * 1.8, 40e-3 * 2, 
                       425, FrameCoordinate(1.0 / 2, 5400.0 / 2))

# The time table data comes from Eugene's SDS data bible file 
# (ECOSTRESS_SDS_Data_Bible.xls in ecostress-sds git repository). The
# real camera is a bit complicated, but we collect about 241 samples
# of data (in along track direction) every 1.181 seconds. For a
# pushbroom, we can divide this up evenly as an approximation. But
# then there is an averaging step (which I don't know the details of) 
# that combines 2 pixels. So we have the factor of 2 given. Scene has 
# 5400 pixels, which is where time calcuation comes from.

tspace = 1.181 / 241 * 2
toff = 5400 * tspace / 2
tlen = 5400 * tspace
# Bug that we seem to need to do this to force spice to be loaded before
# we create the pool. Would like to figure out why this happens and fix this
SpiceHelper.spice_setup()
pool = Pool(20)
for s in range(nscene[pass_index]):
    tt = ConstantSpacingTimeTable(pass_time[pass_index] - toff + tspace +
                                  s * tlen, 
                                  pass_time[pass_index] + toff + s * tlen,
                                  tspace)
    fname = ecostress_file_name("L1B_RAD", orbit_num[pass_index], s + 1, tt.min_time)
    t = L1bRadSimulate(orb, tt, cam, sdata, raycast_resolution = 100.0)
    t.create_file(fname, pool = pool)

# Probably don't want these long term, but save for now
if(False):
    write_shelve("orbit.xml", orb)
    write_shelve("camera.xml", cam)
    write_shelve("time_table.xml", tt)

# fout = h5py.File("ECOSTRESS_L1A_RAW_ATT_800001_00001_20151024020211_0100_01.h5", "w")
# g = fout.create_group("DummyData")
# t = g.create_dataset("README", data = "This is a placeholder")
# t = g.create_dataset("orbit_xml", data = serialize_write_string(orb))
# fout = h5py.File("ECOSTRESS_L1A_BB_800001_00001_20151024020211_0100_01.h5", "w")
# g = fout.create_group("DummyData")
# t = g.create_dataset("README", data = "This is a placeholder")
# fout = h5py.File("ECOSTRESS_L1A_RAW_800001_00001_20151024020211_0100_01.h5", "w")
# g = fout.create_group("DummyData")
# t = g.create_dataset("README", data = "This is a placeholder")
# t = g.create_dataset("tt_xml", data = serialize_write_string(tt))

