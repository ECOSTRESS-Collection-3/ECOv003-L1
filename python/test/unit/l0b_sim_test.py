from .l0b_sim import *
from test_support import *
import os

@slow
def test_l0_simulate(isolated_dir, indir):
    # Temporary, we are using data in a different directory. We'll get this
    # synced up with our other test data in the future
    indir = "/project/test/eyc/l1a_raw_tests/ref/"
    scene_file = \
[ ["1",
   indir + "L1A_RAW_PIX_80005_001_20150124T204251_0100_01.h5",
   indir + "ECOSTRESS_L1A_BB_80005_001_20150124T204251_0100_01.h5"],
  ["2",
   indir + "L1A_RAW_PIX_80005_002_20150124T204346_0100_01.h5",
   indir + "ECOSTRESS_L1A_BB_80005_002_20150124T204346_0100_01.h5"],
  ["3",
   indir + "L1A_RAW_PIX_80005_003_20150124T204441_0100_01.h5",
   indir + "ECOSTRESS_L1A_BB_80005_003_20150124T204441_0100_01.h5"]
]
    raw_att = indir + "L1A_RAW_ATT_80005_20150124T204251_0100_01.h5"
    eng = indir + "ECOSTRESS_L1A_ENG_80005_20150124T204251_0100_01.h5"
    l0_sim = L0BSimulate(raw_att, eng, scene_file)
    l0_sim.create_file("ECOSTRESS_L0B_20150124T204251_20150124T204536_0100_01.h5")
