from .l1a_raw_att_simulate import *
from test_support import *
import os

@slow
def test_l1a_raw_att_simulate(isolated_dir, igc):
    l1a_raw_att_sim = L1aRawAttSimulate(igc.orbit, igc.time_table.min_time,
                                        igc.time_table.max_time)
    l1a_raw_att_sim.create_file("ECOSTRESS_L1A_RAW_ATT_80005_20150124_144252_0100_01.h5")
    
    
    



