from .l0_simulate import *
from test_support import *
import os

@slow
def test_l0_simulate(isolated_dir, test_data):
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
    



