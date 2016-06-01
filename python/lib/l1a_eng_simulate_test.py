from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from l1a_eng_simulate import *
import os

def test_l1a_eng_simulate():
    raise SkipTest  # Don't normally run this, it takes a while
    l1a_eng_sim = L1aEngSimulate()
    l1a_eng_sim.create_file("ECOSTRESS_L1A_ENG_80005_20150124_144252_0100_01.h5")
    
    



