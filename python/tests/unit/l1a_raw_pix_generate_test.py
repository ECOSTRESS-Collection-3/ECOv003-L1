from ecostress.l1a_raw_pix_generate import L1aRawPixGenerate
from geocal import Time
import pytest


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
