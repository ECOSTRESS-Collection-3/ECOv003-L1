from .l1b_rad_generate import *
from test_support import *

def test_l1b_rad_generate(isolated_dir, test_data):
    l1a_pix = test_data + "ECOSTRESS_L1A_PIX_80005_001_20150124T204251_0100_02.h5.expected"
    l1a_gain = test_data + "L1A_GAIN_80005_001_20150124T204251_0100_02.h5.expected"
    l1brad = L1bRadGenerate(l1a_pix, l1a_gain,
                            "ECOSTRESS_L1B_RAD_80005_001_20150124T204251_0100_01.h5")
    l1brad.run()

def test_band_diff(igc):
    write_shelve("igc.xml", igc)
    

