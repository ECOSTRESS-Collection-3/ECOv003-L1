from ecostress.l0b_sim import L0BSimulate
import pytest


@pytest.mark.long_test
def test_l0_simulate(isolated_dir, test_data):
    scene_file = [
        [
            "1",
            str(
                test_data / "L1A_RAW_PIX_80005_001_20150124T204250_0100_01.h5.expected"
            ),
            str(
                test_data
                / "ECOSTRESS_L1A_BB_80005_001_20150124T204250_0100_01.h5.expected"
            ),
        ],
        [
            "2",
            str(
                test_data / "L1A_RAW_PIX_80005_002_20150124T204342_0100_01.h5.expected"
            ),
            str(
                test_data
                / "ECOSTRESS_L1A_BB_80005_002_20150124T204342_0100_01.h5.expected"
            ),
        ],
        [
            "3",
            str(
                test_data / "L1A_RAW_PIX_80005_003_20150124T204434_0100_01.h5.expected"
            ),
            str(
                test_data
                / "ECOSTRESS_L1A_BB_80005_003_20150124T204434_0100_01.h5.expected"
            ),
        ],
    ]
    raw_att = str(test_data / "L1A_RAW_ATT_80005_20150124T204250_0100_01.h5.expected")
    eng = str(test_data / "ECOSTRESS_L1A_ENG_80005_20150124T204250_0100_01.h5.expected")
    l0_sim = L0BSimulate(
        raw_att, eng, scene_file, osp_dir=str(test_data / "l1_osp_dir")
    )
    l0_sim.create_file("ECOSTRESS_L0B_20150124T204251_20150124T204536_0100_01.h5")
