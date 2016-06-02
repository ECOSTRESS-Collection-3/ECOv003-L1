from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l0_simulate import *
import os

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = os.path.dirname(__file__) + "/../../end_to_end_testing/"

def test_l0_simulate():
    raise SkipTest  # Don't normally run this, it takes a while
    scene_file = \
{ "1" :
  [test_data + "ECOSTRESS_L1A_RAW_PIX_80005_001_20150124_144252_0100_01.h5",
   test_data + "ECOSTRESS_L1A_BB_80005_001_20150124_144252_0100_01.h5"],
  "2":
  [test_data + "ECOSTRESS_L1A_RAW_PIX_80005_002_20150124_144345_0100_01.h5",
   test_data + "ECOSTRESS_L1A_BB_80005_002_20150124_144345_0100_01.h5"],
  "3":
  [test_data + "ECOSTRESS_L1A_RAW_PIX_80005_003_20150124_144438_0100_01.h5",
   test_data + "ECOSTRESS_L1A_BB_80005_003_20150124_144438_0100_01.h5"]
}
    raw_att = test_data + "ECOSTRESS_L1A_RAW_ATT_80005_20150124_144252_0100_01.h5"
    eng = test_data + "ECOSTRESS_L1A_ENG_80005_20150124_144252_0100_01.h5"
    l0_sim = L0Simulate(raw_att, eng, scene_file)
    l0_sim.create_file("ECOSTRESS_L0_20150124_144252_0100_01.h5")
    



