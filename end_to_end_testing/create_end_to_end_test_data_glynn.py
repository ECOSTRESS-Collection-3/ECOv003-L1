# This creates test data end to end.
# This is adapted to work with Glynns test data. This is *almost* orbit 80005
# scene 3 but with a few tweaks to cover Glynn's data better.
#
# Note we will call this 80006, just to have a separate name.

from geocal import *
from ecostress import *
import h5py
from multiprocessing import Pool

# Often during development of test data we want to only regenerate
# a subset of the files, using the existing test data instead. Here we
# can just turn each thing on or off. To regenerate everything, this
# should all be True
create_l1a_pix = True
create_l1a_bb = True
create_l1a_raw_pix = True
create_l1a_raw_att = True
create_l1a_eng = True
create_l0b = True
gain_fname = "../../ecostress-test-data/latest/L1A_RAD_GAIN_80005_001_20150124T204250_0100_02.h5.expected"
#gain_fname = None
osp_dir= "../../ecostress-test-data/latest/l1_osp_dir"

orbit_num = 80006

# This offset comes from multiplying through the matrices in the ATBD together.
# I doubt if we will have the accuracy to update these values, but we could
# in principle improve these by doing a camera calibration. Note that the
# offset is ~22 meter on the ground, so it is significant to include but not
# huge compared to our ~70m pixel size and 50m geolocation requirement.
x_offset_iss = np.array([10.8639, -19.2647, 7.0221])

# By bad luck, we picked orbit times in some case that are an night.
# Allow an offset to the reported time so we can "pretend" that the data
# is really during the day. This really only affects the solar angles, and
# allows us to generate solar angles that are somewhat reasonable for passing
# to Level 2.

time_shift = 6 * 60 * 60
orb_iss = OrbitTimeShift(SpiceOrbit(SpiceOrbit.ISS_ID, "iss_spice/iss_2015.bsp"),
                     time_shift)
orb = OrbitScCoorOffset(orb_iss, x_offset_iss)

aster_mosaic_dir = "/project/ancillary/ASTER/CAMosaic/"
if(not os.path.exists(aster_mosaic_dir)):
    # Location on pistol
    aster_mosaic_dir = "/data/smyth/AsterMosaic/"
if(not os.path.exists(aster_mosaic_dir)):
    raise RuntimeError("Can't find location of aster mosaic")
glynn_dir = "/project/test/ASTER/EndToEndTest/latest/eco-sim/"
if(not os.path.exists(glynn_dir)):
    # Location on pistol
    glynn_dir = "/data/smyth/ecostress-test-data/latest/eco-sim/"
if(not os.path.exists(glynn_dir)):
    raise RuntimeError("Can't find location of Glynn's test data")
    
# Use ASTER mosaic for SW, but Glynn's files for the other data
sdata = [VicarLiteRasterImage(aster_mosaic_dir + "calnorm_b%d.img" %
                              ecostress_to_aster_band()[0], 1,
                              VicarLiteFile.READ, 10000, 10000)]
sdata.extend([VicarLiteRasterImage(glynn_dir + "glynn_b%d.img" % (b+1), 1,
                                   VicarLiteFile.READ, 10000, 10000)
              for b in range(5)])

# False here says it ok for SrtmDem to not have tile. This gives support
# for data that is over the ocean.
dem = SrtmDem("",False)
sm = EcostressScanMirror()

# Camera comes from the separate ecostress_camera_generate.py script
cam = read_shelve("camera_20180208.xml")

# Time of start. This was determined as the time of 80005 scene 3, minus a
# fudge factor to cover Glynn's data.

#tstart = geocal.Time.parse_time("2015-01-24T20:44:41.626764Z") - 7
tstart = geocal.Time.parse_time("2015-01-24T20:44:41.626764Z") - 10
pool = Pool(20)

tt = EcostressTimeTable(tstart, False)
igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
start_time = tt.min_time
end_time = tt.max_time
scene_files = []
l1a_pix_fname = ecostress_file_name("L1A_PIX", orbit_num, 1, tt.min_time)
l1a_pix_sim = L1aPixSimulate(igc, sdata, gain_fname = gain_fname)
if(create_l1a_pix):
    l1a_pix_sim.create_file(l1a_pix_fname, pool=pool)
    
l1a_bb_fname = ecostress_file_name("L1A_BB", orbit_num, 1, tt.min_time)
l1a_bb_sim = L1aBbSimulate(l1a_pix_fname)
if(create_l1a_bb):
    l1a_bb_sim.create_file(l1a_bb_fname)

l1a_raw_pix_fname = ecostress_file_name("L1A_RAW_PIX", orbit_num, 1,
                                        tt.min_time, intermediate=True)
l1a_raw_pix_sim = L1aRawPixSimulate(l1a_pix_fname)
if(create_l1a_raw_pix):
    l1a_raw_pix_sim.create_file(l1a_raw_pix_fname)
scene_files.append([1, l1a_raw_pix_fname, l1a_bb_fname,
                    orbit_num, tt.min_time, tt.max_time])
    
l1a_raw_att_fname = \
   ecostress_file_name("L1A_RAW_ATT", orbit_num, None, start_time,
                       intermediate=True)
l1a_raw_att_sim = L1aRawAttSimulate(orb_iss, start_time, end_time)
if(create_l1a_raw_att):
    l1a_raw_att_sim.create_file(l1a_raw_att_fname)

l1a_eng_fname = ecostress_file_name("L1A_ENG", orbit_num, None,
                                    start_time)
l1a_eng_sim = L1aEngSimulate(l1a_raw_att_fname)
if(create_l1a_eng):
    l1a_eng_sim.create_file(l1a_eng_fname)

l0b_fname = ecostress_file_name("L0B", orbit_num, None, start_time, end_time, intermediate=True)
scene_fname = ecostress_file_name("Scene", orbit_num, None,
                                  start_time, end_time, extension=".txt",
                                  intermediate=True)
# Level 0 seems to need to have a buffer in the scene file, so add some pad
with open(scene_fname, "w") as fh:
    for s, fname1, fname2, orb, tstart, tend in scene_files:
        print("%d %03d %s %s" % (orb, s, tstart-3, tend+3), file=fh)
l0b_sim = L0BSimulate(l1a_raw_att_fname, l1a_eng_fname, scene_files,
                      osp_dir=osp_dir)
if(create_l0b):
    l0b_sim.create_file(l0b_fname)
    


