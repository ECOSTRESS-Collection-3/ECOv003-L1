from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l1a_raw_pix_generate import *
import os
# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
if("end_to_end_test_data" in os.environ):
    test_data = os.environ["end_to_end_test_data"] + "/"
else:
    test_data = "/project/ancillary/ASTER/EndToEndTest/latest/"

l0 = test_data + "ECOSTRESS_L0_20150124_144252_0100_01.h5"

def test_l1a_raw_pix_generate():
    #raise SkipTest              # Don't normally run this, it generates a lot
                                # of ouput
    l1arawpix = L1aRawPixGenerate(l0)
    l1arawpix.run()



