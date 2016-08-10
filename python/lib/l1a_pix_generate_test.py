from .l1a_pix_generate import *
from test_support import *
import os

def test_l1a_pix_generate(isolated_dir, test_data):
    fvar = "80005_001_20150124T144252_0100_01.h5.expected"
    l1a_bb = test_data + "ECOSTRESS_L1A_BB_" + fvar
    l1a_raw = test_data + "ECOSTRESS_L1A_RAW_PIX_" + fvar
    l1apix = L1aPixGenerate(l1a_bb, l1a_raw, "l1a_pix.h5",
                            local_granule_id = "ECOSTRESS_L1A_PIX_" + fvar)
    l1apix.run()



