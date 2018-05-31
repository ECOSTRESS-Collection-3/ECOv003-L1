from .l1b_proj import *
from geocal import IgcArray
from test_support import *
from multiprocessing import Pool

# Don't normally run, this takes about 1 minute with 10 processors
@slow
def test_l1b_proj(isolated_dir, igc_with_img):
    ortho = [Landsat7Global("/raid22", Landsat7Global.BAND5),
             Landsat7Global("/raid22", Landsat7Global.BAND5)]
    igccol = IgcArray([], False)
    igccol.add_igc(igc_with_img)
    igccol.add_igc(igc_with_img)
    p = L1bProj(igccol, ["proj1.img", "proj2.img"],
                ["ref1.img", "ref2.img"], ortho)
    pool = Pool(20)
    p.proj(pool=pool)

    
