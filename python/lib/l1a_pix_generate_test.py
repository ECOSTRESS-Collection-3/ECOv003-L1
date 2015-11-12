from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l1a_pix_generate import *

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = "/project/ancillary/ASTER/EndToEndTest/"

l1a_bb = test_data + "ECOSTRESS_L1A_BB_800001_00001_20151024020211_0100_01.h5"
l1a_raw = test_data + "ECOSTRESS_L1A_RAW_800001_00001_20151024020211_0100_01.h5"

def test_l1a_pix_generate():
    l1apix = L1aPixGenerate(l1a_bb, l1a_raw, "l1a_pix.h5")
    l1apix.run()



