# This creates test data end to end. This is the content of the
# original notebook we used, put into a script that is easier to 
# run in the future.

from geocal import *
import h5py

if(False):
    # Only on pistol
    f = VicarLiteRasterImage("/raid27/tllogan/ecostress/coregtst/calnorm_b4.img")
    f = SubRasterImage(f,0,0,37000, 40000)

# We inspected http://heavens-above.com looking for tracks that look
# like it goes near this point. It looks like oneof the passes from
# 10/23/2015 (PST) looks pretty good for this. Note also data 10/3/2015 
# which goes across the other way, if we need to use that instead.

# Time here is the maximum altitude for our point. It is given in 
# local time, so we need to convert to UTC

t = Time.parse_time('2015-10-23T19:02:38Z') + 7 * 60 * 60

# TLE comes from http://www.n2yo.com/satellite/?s=25544. This was 
# for 10/24/2015

tle = '''\
1 25544U 98067A   15301.64187079  .00010243  00000-0  15860-3 0  9995
2 25544  51.6438 138.0120 0006887  88.7083 356.4634 15.54663652968802
'''
orb = TleOrbit(tle)

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
band = 0
tspace = 1.181 / 241 * 2
toff = 5400 * tspace / 2
tt = ConstantSpacingTimeTable(t - toff + tspace, t + toff, tspace)
ipi = Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
igc = IpiImageGroundConnection(ipi, dem, None)

print distance(igc.ground_coordinate(ImageCoordinate(1, 5400 / 2)),
               igc.ground_coordinate(ImageCoordinate(1, 1 + 5400 / 2)))
print distance(igc.ground_coordinate(ImageCoordinate(1, 5400 / 2)),
               igc.ground_coordinate(ImageCoordinate(2, 5400 / 2)))
print igc.footprint_resolution(1, 5400 / 2)

# We may want to have IgcSimulated not read everything into memory. But 
# start with this

#write_shelve("test_data.db:igc_simulated", IgcSimulated(igc, f, -1, False))
# Maybe the following instead?
#write_shelve("igc_simulated.xml", IgcSimulated(igc, f, -1, False))

# Then do write_image --verbose --number-process=20 
# --process-number-line=100 --process-number-sample=100 
# test_data.db:igc_simulated l1b1_sim.img "


write_shelve("orbit.xml", orb)
write_shelve("camera.xml", cam)
write_shelve("time_table.xml", tt)

fout = h5py.File("ECOSTRESS_L1A_RAW_ATT_800001_00001_20151024020211_0100_01.h5", "w")
g = fout.create_group("DummyData")
t = g.create_dataset("README", data = "This is a placeholder")
t = g.create_dataset("orbit_xml", data = serialize_write_string(orb))
fout = h5py.File("ECOSTRESS_L1A_BB_800001_00001_20151024020211_0100_01.h5", "w")
g = fout.create_group("DummyData")
t = g.create_dataset("README", data = "This is a placeholder")
fout = h5py.File("ECOSTRESS_L1A_RAW_800001_00001_20151024020211_0100_01.h5", "w")
g = fout.create_group("DummyData")
t = g.create_dataset("README", data = "This is a placeholder")
t = g.create_dataset("tt_xml", data = serialize_write_string(tt))

