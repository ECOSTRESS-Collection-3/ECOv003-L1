from ecostress.l1a_eng_simulate import L1aEngSimulate
import pytest


@pytest.mark.long_test
def test_l1a_eng_simulate(isolated_dir, test_data):
    fname = str(test_data / "L1A_RAW_ATT_80005_20150124T204250_0100_01.h5.expected")
    l1a_eng_sim = L1aEngSimulate(fname)
    l1a_eng_sim.create_file("ECOSTRESS_L1A_ENG_80005_20150124T144252_0100_01.h5")
