from ecostress.l1b_proj import L1bProj
from geocal import IgcArray
from multiprocessing import Pool
import pytest


@pytest.mark.long_test
def test_l1b_proj(isolated_dir, igc_with_img, ortho):
    igccol = IgcArray([], False)
    igccol.add_igc(igc_with_img)
    igccol.add_igc(igc_with_img)
    p = L1bProj(
        igccol, ["proj1.img", "proj2.img"], ["ref1.img", "ref2.img"], [ortho, ortho]
    )
    pool = Pool(20)
    p.proj(pool=pool)


@pytest.mark.long_test
def test_l1b_scan_proj(isolated_dir, igc_with_img, ortho):
    igccol = IgcArray([], False)
    igccol.add_igc(igc_with_img)
    p = L1bProj(
        igccol, ["proj1.img"], ["ref1.img"], [ortho], separate_file_per_scan=True
    )
    pool = Pool(20)
    p.proj(pool=pool)
