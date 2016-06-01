from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l1a_raw_pix_simulate import *
import os

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = os.path.dirname(__file__) + "/../../end_to_end_testing/"
fname = test_data + "ECOSTRESS_L1A_PIX_80005_001_20150124_144252_0100_01.h5"

def test_l1a_bb_simulate():
    raise SkipTest  # Don't normally run this, it takes a while
    l1a_raw_pix_sim = L1aRawPixSimulate(fname)
    l1a_raw_pix_sim.create_file("ECOSTRESS_L1A_RAW_PIX_80005_001_20150124_144252_0100_01.h5")
    



