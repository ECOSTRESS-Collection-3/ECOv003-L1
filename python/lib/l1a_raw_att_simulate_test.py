from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l1a_raw_att_simulate import *
import os

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = os.path.dirname(__file__) + "/../../end_to_end_testing/"
orb = read_shelve(test_data + "orbit.xml")
tt = read_shelve(test_data + "time_table.xml")

def test_l1a_raw_att_simulate():
    raise SkipTest  # Don't normally run this, it takes a while
    l1a_raw_att_sim = L1aRawAttSimulate(orb, tt.min_time, tt.max_time)
    l1a_raw_att_sim.create_file("ECOSTRESS_L1A_RAW_ATT_80005_20150124_144252_0100_01.h5")
    
    
    



