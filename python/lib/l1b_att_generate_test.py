from .l1b_att_generate import *
from test_support import *

def test_l1b_att_generate(isolated_dir, igc, orb_fname):
    tatt = [igc.time_table.time(ImageCoordinate(i,0))[0] for i in range(0,44*128, 128)]
    teph = tatt
    l1batt = L1bAttGenerate(orb_fname, igc.orbit, "l1b_att.h5", tatt, teph, [],
                            local_granule_id = "ECOSTRESS_L1B_ATT_80001_001_20151024_020211_0100_01.h5")
    l1batt.run()




