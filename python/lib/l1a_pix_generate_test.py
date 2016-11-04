from .l1a_pix_generate import *
from .exception import VicarRunException
from test_support import *
import os

def test_l1a_pix_generate(isolated_dir, test_data, vicar_path):
    fvar = "80005_001_20150124T204251_0100_01.h5"
    fvar2 = "80005_20150124T204251_0100_01.h5.expected"
    l1a_bb = test_data + "ECOSTRESS_L1A_BB_" + fvar + ".expected"
    l1a_raw = test_data + "L1A_RAW_PIX_" + fvar + ".expected"
    l1_osp_dir = test_data + "l1_osp_dir"
    l1a_eng = test_data + "ECOSTRESS_L1A_ENG_" + fvar2
    log = open("test.log", "w")
    l1apix = L1aPixGenerate(l1a_bb, l1a_raw, l1a_eng, l1_osp_dir,
                            "ECOSTRESS_L1A_PIX_" + fvar,
                            "L1A_GAIN_" + fvar,
                            quiet=True, log = log)
    l1apix.run()

def test_l1a_pix_generate_failed(isolated_dir, test_data, vicar_path):
    fvar = "80005_001_20150124T204251_0100_01.h5"
    fvar2 = "80005_20150124T204251_0100_01.h5.expected"
    l1a_bb = test_data + "ECOSTRESS_L1A_BB_" + fvar + ".expected"
    l1a_raw = test_data + "L1A_RAW_PIX_" + fvar + ".expected"
    l1_osp_dir = test_data + "l1_osp_dir"
    l1a_eng = test_data + "ECOSTRESS_L1A_ENG_" + fvar2
    log = open("test.log", "w")
    # Pass in bad file name, to make sure we correctly handle a failed
    # job.
    l1apix = L1aPixGenerate("bad_bb_data", l1a_raw, l1a_eng, l1_osp_dir,
                            "ECOSTRESS_L1A_PIX_" + fvar,
                            "L1A_GAIN_" + fvar,
                            quiet=True, log = log)
    with pytest.raises(VicarRunException):
        l1apix.run()
    


