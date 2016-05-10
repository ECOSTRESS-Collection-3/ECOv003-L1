from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from geocal import *
from l1b_geo_generate import *
from multiprocessing import Pool

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = os.path.dirname(__file__) + "/../../end_to_end_testing/"

orb = read_shelve(test_data + "orbit_old.xml")
cam = read_shelve(test_data + "camera.xml")
tt = read_shelve(test_data + "time_table_old.xml")
band = 0
ipi = Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
# False here says it ok for SrtmDem to not have tile. This gives support
# for data that is over the ocean.
dem = SrtmDem("",False)
igc = IpiImageGroundConnection(ipi, dem, None)

def test_l1b_geo_generate():
    # Only do 100 lines so this runs quickly as a test
    l1bgeo = L1bGeoGenerate(igc, "l1b_geo.h5", number_line = 100)
    pool = Pool(10)
    l1bgeo.run(pool)



