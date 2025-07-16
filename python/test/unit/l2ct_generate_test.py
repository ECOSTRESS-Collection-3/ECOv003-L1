from ecostress import L2ctGenerate
import pytest
from multiprocessing import Pool


@pytest.mark.long_test
def test_l2ct_generate(isolated_dir, test_data_latest, lwm):
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1cg = test_data_latest / "ECOv003_L1CG_RAD_03129_002_20190124T012016_0800_01.h5"
    l2cg_lste = (
        test_data_latest / "ECOv003_L2G_LSTE_03129_002_20190124T012016_7999_97.h5"
    )
    out_pattern = "ECOv003_L2T_LSTE_03129_002_TILE_20190124T012016_0100_01"
    g = L2ctGenerate(
        l1cg,
        l2cg_lste,
        l1_osp_dir,
        out_pattern,
        [
            "fake_input.h5",
        ],
    )
    if True:
        pool = Pool(5)
    else:
        pool = None
    g.run(pool=pool)
    if pool is not None:
        pool.close()
