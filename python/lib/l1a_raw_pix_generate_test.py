from .l1a_raw_pix_generate import *
from test_support import *
import os


def test_l1a_raw_pix_generate(isolated_dir, test_data):
    l0 = test_data + "ECOSTRESS_L0_20150124_144252_0100_01.h5"
    l1arawpix = L1aRawPixGenerate(l0)
    l1arawpix.run()



