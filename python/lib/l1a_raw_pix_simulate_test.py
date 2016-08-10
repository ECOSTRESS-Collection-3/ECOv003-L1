from .l1a_raw_pix_simulate import *
from test_support import *
import os

@slow
def test_l1a_bb_simulate(isolated_dir, test_data):
    raise SkipTest  # Don't normally run this, it takes a while
    fname = test_data + "ECOSTRESS_L1A_PIX_80005_001_20150124T144252_0100_01.h5"
    l1a_raw_pix_sim = L1aRawPixSimulate(fname)
    l1a_raw_pix_sim.create_file("ECOSTRESS_L1A_RAW_PIX_80005_001_20150124T144252_0100_01.h5")
    



