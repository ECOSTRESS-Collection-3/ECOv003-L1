from ecostress.l1a_raw_pix_simulate import L1aRawPixSimulate
import pytest


@pytest.mark.long_test
def test_l1a_bb_simulate(isolated_dir, test_data):
    fname = str(
        test_data / "ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_02.h5.expected"
    )
    l1a_raw_pix_sim = L1aRawPixSimulate(fname)
    l1a_raw_pix_sim.create_file(
        "ECOSTRESS_L1A_RAW_PIX_80005_001_20150124T144252_0100_01.h5"
    )
