# This creates test data end to end.
from geocal import *
from ecostress import *
import h5py
from multiprocessing import Pool

# Often during development of test data we want to only regenerate
# a subset of the files, using the existing test data instead. Here we
# can just turn each thing on or off. To regenerate everything, this
# should all be True
create_l1a_pix = False
create_l1a_bb = False
create_l1a_raw_pix = False
create_l1a_raw_att = True
create_l1a_eng = True
create_l0b = True

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
# Allow an offset to the reported time so we can "pretend" that the data
# is really during the day. This really only affects the solar angles, and
# allows us to generate solar angles that are somewhat reasonable for passing
# to Level 2.

time_shift = [0, 0, 0, 0, 6 * 60 * 60]

pass_index = 4 # The pass we are working with

aster_mosaic_dir = "/project/ancillary/ASTER/CAMosaic/"
if(not os.path.exists(aster_mosaic_dir)):
    # Location on pistol
    aster_mosaic_dir = "/data/smyth/AsterMosaic/"
if(not os.path.exists(aster_mosaic_dir)):
    raise RuntimeError("Can't find location of aster mosaic")

# Get the ASTER mosaic we are working with for all the bands. The
# bands comes from the wiki. Data originally comes from /raid11/astermos,
# but is compressed there.
sdata = [VicarLiteRasterImage(aster_mosaic_dir + "calnorm_b%d.img" % b, 1,
                              VicarLiteFile.READ, 1000, 1000)
         for b in [14,14,12,11,10,4]]

orb = OrbitTimeShift(SpiceOrbit(SpiceOrbit.ISS_ID, "iss_spice/iss_2015.bsp"),
                     time_shift[pass_index])
# False here says it ok for SrtmDem to not have tile. This gives support
# for data that is over the ocean.
dem = SrtmDem("",False)
sm = EcostressScanMirror()

# Camera comes from the separate ecostress_camera_generate.py script
cam = read_shelve("camera.xml")
# ***********************************
# Need to fix this time calculation
# ***********************************
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
scene_files = []
pool = Pool(20)
for s in range(nscene[pass_index]):
    tstart = pass_time[pass_index] - toff + tspace + \
             s * tlen + time_shift[pass_index]
    tt = EcostressTimeTable(tstart, False)
    igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    # Save this for use in making the L0 and orbit based file name
    if(s == 0):
        start_time = tt.min_time
        # Probably don't want these long term, but save for now
        if(True):
            write_shelve("orbit.xml", orb)
            write_shelve("camera.xml", cam)
            write_shelve("time_table.xml", tt)
    if(s == nscene[pass_index] - 1):
        end_time = tt.max_time
    l1a_pix_fname = ecostress_file_name("L1A_PIX", orbit_num[pass_index],
                                        s + 1, tt.min_time)
    l1a_pix_sim = L1aPixSimulate(igc, sdata)
    if(create_l1a_pix):
        l1a_pix_sim.create_file(l1a_pix_fname, pool=pool)
    
    l1a_bb_fname = ecostress_file_name("L1A_BB", orbit_num[pass_index],
                                       s + 1, tt.min_time)
    l1a_bb_sim = L1aBbSimulate(l1a_pix_fname)
    if(create_l1a_bb):
        l1a_bb_sim.create_file(l1a_bb_fname)

    l1a_raw_pix_fname = \
     ecostress_file_name("L1A_RAW_PIX", orbit_num[pass_index], s + 1,
                         tt.min_time, intermediate=True)
    l1a_raw_pix_sim = L1aRawPixSimulate(l1a_pix_fname)
    if(create_l1a_raw_pix):
        l1a_raw_pix_sim.create_file(l1a_raw_pix_fname)
    scene_files.append([s+1, l1a_raw_pix_fname, l1a_bb_fname,
                        orbit_num[pass_index], tt.min_time, tt.max_time])
    
l1a_raw_att_fname = \
   ecostress_file_name("L1A_RAW_ATT", orbit_num[pass_index], None, start_time,
                       intermediate=True)
l1a_raw_att_sim = L1aRawAttSimulate(orb, start_time, end_time)
if(create_l1a_raw_att):
    l1a_raw_att_sim.create_file(l1a_raw_att_fname)

l1a_eng_fname = ecostress_file_name("L1A_ENG", orbit_num[pass_index], None,
                                    start_time)
l1a_eng_sim = L1aEngSimulate()
if(create_l1a_eng):
    l1a_eng_sim.create_file(l1a_eng_fname)

l0b_fname = ecostress_file_name("L0B", None, None, start_time, end_time)
scene_fname = ecostress_file_name("Scene", orbit_num[pass_index], None,
                                  start_time, end_time, extension=".txt",
                                  intermediate=True)
l0b_sim = L0BSimulate(l1a_raw_att_fname, l1a_eng_fname, scene_files)
if(create_l0b):
    l0b_sim.create_file(l0b_fname)
    


