from .l1a_raw_att_simulate import *
from .misc import ecostress_file_name
from test_support import *
import os
from geocal import read_shelve

@slow
def test_l1a_raw_att_simulate(isolated_dir, test_data):
    orb = read_shelve(test_data + "l1_osp_dir/orbit.xml")
    tt = read_shelve(test_data + "l1_osp_dir/time_table.xml")
    l1a_raw_att_sim = L1aRawAttSimulate(orb, tt.min_time, tt.max_time)
    l1a_raw_att_fname = ecostress_file_name("L1A_RAW_ATT", 80005, None,
                                            tt.min_time)
    l1a_raw_att_sim.create_file(l1a_raw_att_fname)
    
    
    



