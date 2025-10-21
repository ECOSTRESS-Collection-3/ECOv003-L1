from ecostress import L1bGeoProcess
from pathlib import Path
import os
import pytest


@pytest.mark.long_test
def test_l1b_geo_process(isolated_dir, test_data_latest):
    l1a_raw_att = test_data_latest / "L1A_RAW_ATT_03663_20190227T094659_01.h5.expected"
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1b_rad = [
        test_data_latest / "ECOv003_L1B_RAD_03663_001_20190227T101222_01.h5.expected",
    ]
    l1bgeo = L1bGeoProcess(
        prod_dir=Path("."),
        l1a_raw_att=l1a_raw_att,
        l1_osp_dir=l1_osp_dir,
        l1b_rad=l1b_rad,
        # When debugging, easier (although slower) to skip parallel processing
        # number_cpu=1,
        # skip_sba=True,
    )
    l1bgeo.run()


# Version that uses a run config file. This isn't normally run (and duplicates
# our end to end test anyways). But nice during development to be able to call
# this version.
@pytest.mark.skip
@pytest.mark.long_test
def test_l1b_geo_process_run_config(test_data_latest):
    os.chdir("/home/smyth/Local/ecostress-build/build_conda")
    # Special flag to override some data found in xml, just so we have
    # a way to do this in testing.
    os.environ["ECOSTRESS_USE_AFIDS_ENV"] = "t"
    run_config = test_data_latest / "ECOSTRESS_L1B_GEO_RunConfig_20190227T0946.xml"
    l1bgeo = L1bGeoProcess(run_config=run_config)
    print(l1bgeo)


# Unit test that we looked at for improving matching
@pytest.mark.long_test
def test_sample_1_l1b_geo_process(isolated_dir, test_data_latest):
    l1a_raw_att = Path(
        "/arcdata/smyth/L1A_RAW_ATT/2025/04/18/L1A_RAW_ATT_38454_20250418T100503_0713_01.h5"
    )
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1b_rad = [
        Path(
            "/arcdata/smyth/L1B_RAD/2025/04/18/ECOv002_L1B_RAD_38454_019_20250418T104749_0713_01.h5"
        )
    ]
    l1bgeo = L1bGeoProcess(
        prod_dir=Path("."),
        l1a_raw_att=l1a_raw_att,
        l1_osp_dir=l1_osp_dir,
        l1b_rad=l1b_rad,
        # When debugging, easier (although slower) to skip parallel processing
        # number_cpu=1,
        # skip_sba=True,
    )
    l1bgeo.run()
