from ecostress import L1cgGenerate
import pytest


@pytest.mark.long_test
def test_l1cg_generate(isolated_dir, test_data_latest, dem, lwm):
    l1b_geo_fname = (
        test_data_latest / "ECOv003_L1B_GEO_03663_001_20190227T101222_01.h5.expected"
    )
    l1b_rad_fname = (
        test_data_latest / "ECOv003_L1B_RAD_03663_001_20190227T101222_01.h5.expected"
    )
    outname = "l1cg_test.h5"
    g = L1cgGenerate(
        l1b_geo_fname,
        l1b_rad_fname,
        dem,
        lwm,
        outname,
        [
            "fake_input.h5",
        ],
        local_granule_id="ECOv003_L1CG_RAD_03663_001_20190227T101222_01.h5",
    )
    g.run()
