from ecostress.l1a_bb_simulate import L1aBbSimulate
import pytest


@pytest.mark.long_test
def test_l1a_bb_simulate(isolated_dir, test_data):
    fname = str(
        test_data / "ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_02.h5.expected"
    )
    l1a_bb_sim = L1aBbSimulate(fname)
    l1a_bb_sim.create_file("ECOSTRESS_L1A_BB_80005_001_20150124T144252_0100_01.h5")
