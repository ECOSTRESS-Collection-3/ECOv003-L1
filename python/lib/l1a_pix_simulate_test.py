from .l1a_pix_simulate import *
from test_support import *
import os

@slow
def test_l1a_pix_simulate(isolated_dir, test_data):
    fname = test_data + "ECOSTRESS_L1B_RAD_80005_001_20150124T144252_0100_01.h5"
    l1a_pix_sim = L1aPixSimulate(fname)
    l1a_pix_sim.create_file("ECOSTRESS_L1A_PIX_80005_001_20150124T144252_0100_01.h5")
    



