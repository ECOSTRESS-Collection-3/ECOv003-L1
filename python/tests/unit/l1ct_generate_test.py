from ecostress import L1ctGenerate
import pytest
from multiprocessing import Pool
from pathlib import Path

@pytest.mark.long_test
def test_l1ct_generate(isolated_dir, test_data_latest, lwm):
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1b_geo_fname = (
        test_data_latest / "ECOv003_L1B_GEO_03663_001_20190227T101223_01.h5.expected"
    )
    l1b_rad_fname = (
        test_data_latest / "ECOv003_L1B_RAD_03663_001_20190227T101223_01.h5.expected"
    )
    out_pattern = "ECOv003_L1CT_RAD_03663_001_TILE_20190227T101222_01"
    g = L1ctGenerate(
        l1b_geo_fname,
        l1b_rad_fname,
        lwm,
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

# A problem case we found in production
@pytest.mark.skip
def test_problem_l1ct_generate(isolated_dir, test_data_latest, lwm):
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    data_path = Path("/project/sandbox/smyth/L1CIssue2")
    l1b_geo_fname = (
        data_path / "ECOv003_L1B_GEO_47124_032_20261027T115800_01.h5"
    )
    l1b_rad_fname = (
        data_path / "ECOv003_L1B_RAD_47124_032_20261027T115800_01.h5"
    )
    out_pattern = "ECOv003_L1CT_RAD_47124_032_TILE_20261027T115800_01"
    g = L1ctGenerate(
        l1b_geo_fname,
        l1b_rad_fname,
        lwm,
        l1_osp_dir,
        out_pattern,
        [
            "fake_input.h5",
        ],
    )
    #if False:
    if True:
        pool = Pool(5)
    else:
        pool = None
    g.run(pool=pool)
    if pool is not None:
        pool.close()
        
