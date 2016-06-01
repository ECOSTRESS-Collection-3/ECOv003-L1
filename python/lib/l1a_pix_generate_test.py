from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l1a_pix_generate import *
import os
# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
if("end_to_end_test_data" in os.environ):
    test_data = os.environ["end_to_end_test_data"] + "/"
else:
    test_data = "/project/ancillary/ASTER/EndToEndTest/latest/"

l1a_bb = test_data + "ECOSTRESS_L1A_BB_80001_001_20151024_020211_0100_01.h5"
l1a_raw = test_data + "ECOSTRESS_L1A_RAW_80001_001_20151024_020211_0100_01.h5"

def test_l1a_pix_generate():
    l1apix = L1aPixGenerate(l1a_bb, l1a_raw, "l1a_pix.h5",
                            local_granule_id = "ECOSTRESS_L1A_RAW_80001_001_20151024_020211_0100_01.h5")
    l1apix.run()



