from ecostress import L1ctGenerate
import pytest
from multiprocessing import Pool


@pytest.mark.long_test
def test_l1ct_generate(isolated_dir, test_data_latest):
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1b_geo_fname = (
        test_data_latest
        / "ECOv002_L1B_GEO_03663_001_20190227T101222_0100_01.h5.expected"
    )
    l1b_rad_fname = (
        test_data_latest
        / "ECOv002_L1B_RAD_03663_001_20190227T101222_0100_01.h5.expected"
    )
    out_pattern = "ECOv002_L1CT_RAD_03663_001_TILE_20190227T101222_0100_01"
    g = L1ctGenerate(l1b_geo_fname, l1b_rad_fname, l1_osp_dir, out_pattern, ["fake_input.h5",])
    if True:
        pool = Pool(20)
    else:
        pool = None
    g.run(pool=pool)
    if pool is not None:
        pool.close()
