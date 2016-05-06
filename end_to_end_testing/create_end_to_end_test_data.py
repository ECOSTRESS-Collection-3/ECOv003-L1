# This creates test data end to end. This is the content of the
# original notebook we used, put into a script that is easier to 
# run in the future.

from geocal import *
import h5py

# Center times for each of the passes. See the wiki at 
# https://wiki.jpl.nasa.gov/display/ecostress/Test+Data and subpages for details

pass_time = [Time.parse_time("2015-01-14T12:00:24.995464Z"),
            Time.parse_time("2015-03-11T13:27:08.758614Z"),
            Time.parse_time("2015-03-02T16:34:33.146760Z"),
            Time.parse_time("2015-04-16T22:13:14.347679Z"),
            Time.parse_time("2015-01-24T14:43:18.819553Z")]
pass_index = 0 # The pass we are working with

# Get the ASTER mosaic we are working with for all the bands. The
# bands comes from the wiki. Data originally comes from /raid11/astermos,
# but is compressed there.
generate_raycasted_data = True
if(generate_raycasted_data):
    # Only on pistol
    def fname(band):
        return "/data/smyth/AsterMosiac/calnorm_b%d.img" % band
    f = [VicarLiteRasterImage(fname(aster_band)) for aster_band in [10, 11, 12, 14, 14, 4]]

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

# False here says it ok for SrtmDem to not have tile. This gives support
# for data that is over the ocean.
dem = SrtmDem("",False)
# Don't treat the bands as different yet, so fix this to a single band
band = 0
tspace = 1.181 / 241 * 2
toff = 5400 * tspace / 2
tt = ConstantSpacingTimeTable(pass_time[pass_index] - toff + tspace, 
                              pass_time[pass_index] + toff, tspace)
ipi = Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
igc = IpiImageGroundConnection(ipi, dem, None)

print(distance(igc.ground_coordinate(ImageCoordinate(1, 5400 / 2)),
               igc.ground_coordinate(ImageCoordinate(1, 1 + 5400 / 2))))
print(distance(igc.ground_coordinate(ImageCoordinate(1, 5400 / 2)),
               igc.ground_coordinate(ImageCoordinate(2, 5400 / 2))))
print(igc.footprint_resolution(1, int(5400 / 2)))

# We may want to have IgcSimulated not read everything into memory. But 
# start with this

if(generate_raycasted_data):
    for b in range(6):
        write_shelve("test_data.db:igc_simulated_p%d_b%d" % (pass_index + 1, b+1), 
                     IgcSimulated(igc, f[b], -1, False))

# Then do 
# write_image --verbose --number-process=20 --process-number-line=100 --process-number-sample=100 test_data.db:igc_simulated_p1_b1 l1b1_sim_p1_b1.img
# And repeat for all bands


# Probably don't want these long term, but save for now
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

