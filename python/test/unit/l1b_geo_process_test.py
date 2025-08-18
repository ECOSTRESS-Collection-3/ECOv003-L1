from ecostress import L1bGeoProcess
import pytest

@pytest.mark.long_test
def test_l1b_geo_process(isolated_dir, test_data):
    l1a_raw_att = test_data / "L1A_RAW_ATT_03663_20190227T094659_0100_01.h5.expected"
    l1_osp_dir = test_data / "l1_osp_dir"
    l1b_rad = [test_data / "ECOv002_L1B_GEO_03663_001_20190227T101222_0100_01.h5.expected",]
    l1bgeo = L1bGeoProcess(l1a_raw_att=l1a_raw_att,
                       l1_osp_dir=l1_osp_dir,
                       l1b_rad=l1b_rad)
    l1bgeo.run()

