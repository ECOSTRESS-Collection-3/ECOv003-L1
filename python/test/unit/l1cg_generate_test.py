from ecostress import L1cgGenerate
import h5py
import pytest


@pytest.mark.long_test
def test_l1cg_generate(isolated_dir, test_data_latest):
    l1b_geo_fname = test_data_latest / "ECOv002_L1B_GEO_03663_001_20190227T101222_0100_01.h5.expected"
    l1b_rad_fname = test_data_latest / "ECOv002_L1B_RAD_03663_001_20190227T101222_0100_01.h5.expected"
    outname = "l1cg_test.h5"
    g = L1cgGenerate(l1b_geo_fname, l1b_rad_fname, outname)
    g.run()
    

