from .l1b_rad_generate import *
from test_support import *

def test_l1b_rad_generate(isolated_dir, igc_hres, dn_fname, gain_fname):
    l1brad = L1bRadGenerate(igc_hres, dn_fname, gain_fname,
                            "ECOSTRESS_L1B_RAD_80005_001_20150124T204251_0100_01.h5")
    l1brad.run()

def test_band_diff(igc_hres):
    write_shelve("igc.xml", igc_hres)
    

