from .l1a_eng_simulate import *
from test_support import *
import os

@slow
def test_l1a_eng_simulate(isolated_dir):
    l1a_eng_sim = L1aEngSimulate()
    l1a_eng_sim.create_file("ECOSTRESS_L1A_ENG_80005_20150124T144252_0100_01.h5")
    
    



