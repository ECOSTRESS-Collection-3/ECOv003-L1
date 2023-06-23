from .l1b_proj import *
from geocal import IgcArray
from test_support import *
from multiprocessing import Pool

# Don't normally run, this takes about 1 minute with 10 processors
@slow
def test_l1b_proj(isolated_dir, igc_with_img, ortho):
    igccol = IgcArray([], False)
    igccol.add_igc(igc_with_img)
    igccol.add_igc(igc_with_img)
    p = L1bProj(igccol, ["proj1.img", "proj2.img"],
                ["ref1.img", "ref2.img"], [ortho,ortho])
    pool = Pool(20)
    p.proj(pool=pool)

@slow
def test_l1b_scan_proj(isolated_dir, igc_with_img, ortho):
    igccol = IgcArray([], False)
    igccol.add_igc(igc_with_img)
    p = L1bProj(igccol, ["proj1.img"],
                ["ref1.img"], [ortho], separate_file_per_scan=True)
    pool = Pool(20)
    p.proj(pool=pool)
    
    
