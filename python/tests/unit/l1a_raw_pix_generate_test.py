from ecostress.l1a_raw_pix_generate import L1aRawPixGenerate
from geocal import Time
import pytest
import subprocess
import os

@pytest.mark.long_test
def test_l1a_raw_pix_generate(isolated_dir, test_data):
    l0b = str(test_data / "L0B_80005_20150124T204251_0100_01.h5")
    obst_dir = str(test_data / "obst_dir")
    l1_osp_dir = str(test_data / "l1_osp_dir")
    scene_file = str(test_data / "Scene_80005_20150124T204251_20150124T204533.txt")
    l1arawpix = L1aRawPixGenerate(l0b, obst_dir, l1_osp_dir, scene_file)
    l1arawpix.run()


def test_process_scene_file(test_data):
    """Process the scene file that we generated, and make sure everything is
    ok"""
    l0b = str(test_data / "L0B_80005_20150124T204251_0100_01.h5")
    obst_dir = str(test_data / "obst_dir")
    l1_osp_dir = str(test_data / "l1_osp_dir")
    scene_file = str(test_data / "Scene_80005_20150124T204251_20150124T204533.txt")
    l1arawpix = L1aRawPixGenerate(l0b, obst_dir, l1_osp_dir, scene_file)
    t = l1arawpix.process_scene_file()
    assert t[0][0] == 80005
    assert t[1][0] == 80005
    assert t[2][0] == 80005
    assert t[0][1] == 1
    assert t[1][1] == 2
    assert t[2][1] == 3
    assert t[0][2] == Time.parse_time("2015-01-24T20:42:51.000000Z")
    assert t[1][2] == Time.parse_time("2015-01-24T20:43:42.200000Z")
    assert t[2][2] == Time.parse_time("2015-01-24T20:44:34.200000Z")
    assert t[0][3] == Time.parse_time("2015-01-24T20:43:42.200000Z")
    assert t[1][3] == Time.parse_time("2015-01-24T20:44:34.200000Z")
    assert t[2][3] == Time.parse_time("2015-01-24T20:45:29.000000Z")


def test_process_scene_file2(test_data, unit_test_data):
    """Look at what was a problem scene file uncovered in the V0.30 testing"""
    l0b = str(test_data / "L0B_80005_20150124T204251_0100_01.h5")
    obst_dir = str(test_data / "obst_dir")
    l1_osp_dir = str(test_data / "l1_osp_dir")
    scene_file = str(unit_test_data / "Scene_problem.txt")
    l1arawpix = L1aRawPixGenerate(l0b, obst_dir, l1_osp_dir, scene_file)
    t = l1arawpix.process_scene_file()
    assert t[0][0] == 80005
    assert t[1][0] == 80005
    assert t[2][0] == 80005
    assert t[0][1] == 1
    assert t[1][1] == 2
    assert t[2][1] == 3
    assert t[0][2] == Time.parse_time("2015-01-24T20:42:51.000000Z")
    assert t[1][2] == Time.parse_time("2015-01-24T20:43:52.000000Z")
    assert t[2][2] == Time.parse_time("2015-01-24T20:44:51.000000Z")
    assert t[0][3] == Time.parse_time("2015-01-24T20:43:51.000000Z")
    assert t[1][3] == Time.parse_time("2015-01-24T20:44:51.000000Z")
    assert t[2][3] == Time.parse_time("2015-01-24T20:45:36.000000Z")

def test_hawaii_orbit_l1a_raw(end_to_end_run_dir, test_data_latest):
    '''This runs a full orbit that we used when testing out geolocation.
    This contains a hawaii scene in the first scene that had poor geolocation
    in collection 2. We will use this to test out the time fixes.'''
    os.environ["AFIDS_DATA"] = "/opt/afids/data"
    os.environ["AFIDS_VDEV_DATA"] = "/opt/afids/data/vdev"
    subprocess.run(["l1a_raw_process",
                      "/arcdata/smyth/L0B/2019/08/23/L0B_06415_20190823T151324_0713_02.h5",
                      "/arcdata/smyth/ObstFile/",
                      "/arcdata/smyth/SceneFile/2019/08/23/Scene_06415_20190823T151325_20190823T163757_20260602T010722.txt",
                      str(test_data_latest / "l1_osp_dir"),
                      str(end_to_end_run_dir / "l1a_raw_06415")])
    
