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

# By bad luck, we picked orbit times in some case that are an night.
# Allow and offset to the reported time so we can "pretend" that the data
# is really during the day. This really only affects the solar angles, and
# allows us to generate solar angles that are somewhat reasonable for passing
# to Level 2.

time_shift = [0, 0, 0, 0, 6 * 60 * 60]

pass_index = 4 # The pass we are working with

# Get the ASTER mosaic we are working with for all the bands. The
# bands comes from the wiki. Data originally comes from /raid11/astermos,
# but is compressed there.
# (data is only on pistol
def fname(band):
    return "/data/smyth/AsterMosiac/calnorm_b%d.img" % band
sdata = [ScaleImage(VicarLiteRasterImage(fname(aster_band), 1, VicarLiteFile.READ,
                                         5000, 5000),
                    aster_radiance_scale_factor()[aster_band-1])
         for aster_band in ecostress_to_aster_band()]

orb = OrbitTimeShift(SpiceOrbit(SpiceOrbit.ISS_ID, "iss_spice/iss_2015.bsp"),
                     time_shift[pass_index])

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
# 5632 lines, which is where time calcuation comes from.

tspace = 1.181 / 241 * 2
toff = 5632 * tspace / 2
tlen = 5632 * tspace
scene_files = {}
# Bug that we seem to need to do this to force spice to be loaded before
# we create the pool. Would like to figure out why this happens and fix this
SpiceHelper.spice_setup()
pool = Pool(20)
for s in range(nscene[pass_index]):
    tt = ConstantSpacingTimeTable(pass_time[pass_index] - toff + tspace +
                                  s * tlen + time_shift[pass_index], 
                                  pass_time[pass_index] + toff + s * tlen +
                                  time_shift[pass_index],
                                  tspace)
    # Save this for use in making the L0 and orbit based file name
    if(s == 0):
        start_time = tt.min_time
        # Probably don't want these long term, but save for now
        if(False):
            write_shelve("orbit.xml", orb)
            write_shelve("camera.xml", cam)
            write_shelve("time_table.xml", tt)
    if(s == nscene[pass_index] - 1):
        end_time = tt.max_time
    l1b_rad_fname = ecostress_file_name("L1B_RAD", orbit_num[pass_index],
                                        s + 1, tt.min_time)
    # Temp false condition, to speed up testing
    if(False):
        l1b_rad_sim = L1bRadSimulate(orb, tt, cam, sdata, raycast_resolution = 100.0)
        l1b_rad_sim.create_file(l1b_rad_fname, pool = pool)

    l1a_pix_fname = ecostress_file_name("L1A_PIX", orbit_num[pass_index],
                                        s + 1, tt.min_time)
    l1a_pix_sim = L1aPixSimulate(l1b_rad_fname)
    l1a_pix_sim.create_file(l1a_pix_fname)
    
    l1a_bb_fname = ecostress_file_name("L1A_BB", orbit_num[pass_index],
                                       s + 1, tt.min_time)
    l1a_bb_sim = L1aBbSimulate(l1a_pix_fname)
    l1a_bb_sim.create_file(l1a_bb_fname)

    l1a_raw_pix_fname = \
     ecostress_file_name("L1A_RAW_PIX", orbit_num[pass_index], s + 1,
                         tt.min_time, intermediate=True)
    l1a_raw_pix_sim = L1aRawPixSimulate(l1a_pix_fname)
    l1a_raw_pix_sim.create_file(l1a_raw_pix_fname)
    scene_files[str(s+1)] = [l1a_raw_pix_fname, l1a_bb_fname]
    
l1a_raw_att_fname = \
   ecostress_file_name("L1A_RAW_ATT", orbit_num[pass_index], None, start_time,
                       intermediate=True)
l1a_raw_att_sim = L1aRawAttSimulate(orb, start_time, end_time)
l1a_raw_att_sim.create_file(l1a_raw_att_fname)

l1a_eng_fname = ecostress_file_name("L1A_ENG", orbit_num[pass_index], None,
                                    start_time)
l1a_eng_sim = L1aEngSimulate()
l1a_eng_sim.create_file(l1a_eng_fname)

l0_fname = ecostress_file_name("L0", None, None, start_time, extension=".raw")
l0_sim = L0Simulate(l1a_raw_att_fname, l1a_eng_fname, scene_files)
l0_sim.create_file(l0_fname)


