from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l1b_rad_generate import *

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = "/project/ancillary/ASTER/EndToEndTest/latest/"

l1a_pix = test_data + "ECOSTRESS_L1A_PIX_80001_001_20151024_020211_0100_01.h5.expected"

def test_l1b_rad_generate():
    l1brad = L1bRadGenerate(l1a_pix, "l1b_rad.h5",
                            local_granule_id = "ECOSTRESS_L1B_RAD_80001_001_20151024_020211_0100_01.h5")

    l1brad.run()



