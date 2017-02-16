from .l1a_pix_simulate import *
from test_support import *
from multiprocessing import Pool
import os

@slow
def test_l1a_pix_simulate(isolated_dir, igc, aster_mosaic_surface_data):
    l1a_pix_sim = L1aPixSimulate(igc, aster_mosaic_surface_data)
    pool = Pool(20)
    l1a_pix_sim.create_file("ECOSTRESS_L1A_PIX_80005_001_20150124T144252_0100_01.h5", pool=pool)
    
    



