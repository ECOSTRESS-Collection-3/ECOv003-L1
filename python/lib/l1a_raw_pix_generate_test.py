from .l1a_raw_pix_generate import *
from test_support import *
import os

@slow
def test_l1a_raw_pix_generate(isolated_dir, test_data):
    l0b = test_data + "ECOSTRESS_L0B_20150124T204251_20150124T204533_0100_01.h5"
    l1_osp_dir = test_data + "l1_osp_dir"
    scene_file = test_data + "Scene_80005_20150124T204251_20150124T204533.txt"
    l1arawpix = L1aRawPixGenerate(l0b, l1_osp_dir, scene_file)
    l1arawpix.run()



