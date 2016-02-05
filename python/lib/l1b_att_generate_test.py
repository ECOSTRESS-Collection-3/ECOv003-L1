from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from geocal import *
from l1b_att_generate import *

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = os.path.dirname(__file__) + "/../../end_to_end_testing/"

orb = read_shelve(test_data + "orbit.xml")
cam = read_shelve(test_data + "camera.xml")
tt = read_shelve(test_data + "time_table.xml")
band = 0
ipi = Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
# False here says it ok for SrtmDem to not have tile. This gives support
# for data that is over the ocean.
dem = SrtmDem("",False)
igc = IpiImageGroundConnection(ipi, dem, None)

def test_l1b_att_generate():
    l1batt = L1bAttGenerate(igc, "l1b_att.h5")
    l1batt.run()




