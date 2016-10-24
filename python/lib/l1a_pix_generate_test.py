from .l1a_pix_generate import *
from test_support import *
import os

def test_l1a_pix_generate(isolated_dir, test_data, vicar_path):
    fvar = "80005_001_20150124T144251_0100_01.h5.expected"
    fvar2 = "80005_20150124T144251_0100_01.h5.expected"
    l1a_bb = test_data + "ECOSTRESS_L1A_BB_" + fvar
    l1a_raw = test_data + "ECOSTRESS_L1A_RAW_PIX_" + fvar
    l1_osp_dir = test_data + "l1_osp_dir"
    l1a_eng = test_data + "ECOSTRESS_L1A_ENG_" + fvar2
    l1apix = L1aPixGenerate(l1a_bb, l1a_raw, l1a_eng, l1_osp_dir, "l1a_pix.h5",
                            local_granule_id = "ECOSTRESS_L1A_PIX_" + fvar)
    l1apix.run()



