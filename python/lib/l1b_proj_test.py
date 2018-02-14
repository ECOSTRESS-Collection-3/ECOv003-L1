from .l1b_proj import *
from test_support import *
from multiprocessing import Pool

# Don't normally run, this takes about 1 minute with 10 processors
@slow
def test_l1b_proj(isolated_dir, igc_with_img):
    p = L1bProj(igc_with_img, "proj.img")
    pool = Pool(10)
    p.proj(pool=pool)
    
