from .l1a_bb_simulate import *
from test_support import *
import os

@slow
def test_l1a_bb_simulate(isolated_dir, test_data):
    fname = test_data + "ECOSTRESS_L1A_PIX_80005_001_20150124_144252_0100_01.h5"
    l1a_bb_sim = L1aBbSimulate(fname)
    l1a_bb_sim.create_file("ECOSTRESS_L1A_BB_80005_001_20150124_144252_0100_01.h5")
    



