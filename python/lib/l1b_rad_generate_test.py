from .l1b_rad_generate import *
from test_support import *

def test_l1b_rad_generate(isolated_dir, test_data):
    l1a_pix = test_data + "ECOSTRESS_L1A_PIX_80005_001_20150124_144252_0100_01.h5.expected"
    l1brad = L1bRadGenerate(l1a_pix, "l1b_rad.h5",
                            local_granule_id = "ECOSTRESS_L1B_RAD_80005_001_20150124_144252_0100_01.h5")
    l1brad.run()



