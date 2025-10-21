from ecostress.l1a_raw_att_simulate import L1aRawAttSimulate
from ecostress.misc import ecostress_file_name
import pytest


@pytest.mark.long_test
def test_l1a_raw_att_simulate(isolated_dir, igc_old, old_test_data):
    orb = igc_old.ipi.orbit
    tt = igc_old.ipi.time_table
    l1a_raw_att_sim = L1aRawAttSimulate(orb, tt.min_time, tt.max_time)
    l1a_raw_att_fname = ecostress_file_name("L1A_RAW_ATT", 80005, None, tt.min_time)
    l1a_raw_att_sim.create_file(l1a_raw_att_fname)
