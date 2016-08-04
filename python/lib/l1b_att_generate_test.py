from .l1b_att_generate import *
from test_support import *

def test_l1b_att_generate(isolated_dir, igc):
    l1batt = L1bAttGenerate(igc, "l1b_att.h5",
                            local_granule_id = "ECOSTRESS_L1B_ATT_80001_001_20151024_020211_0100_01.h5")

    l1batt.run()




