from ecostress import L1bProj, L1bGeoProcess
from pathlib import Path
from geocal import IgcArray
from multiprocessing import Pool
import io
import pytest


@pytest.mark.long_test
def test_l1b_proj(isolated_dir, igc_with_img, ortho, lwm):
    igccol = IgcArray([], False)
    igccol.add_igc(igc_with_img)
    igccol.add_igc(igc_with_img)
    p = L1bProj(
        igccol,
        ["proj1.img", "proj2.img"],
        ["ref1.img", "ref2.img"],
        ["lwm1.img", "lwm2.img"],
        [ortho, ortho],
        lwm,
    )
    pool = Pool(20)
    p.proj(pool=pool, include_mask=True)


@pytest.mark.long_test
def test_l1b_scan_proj(isolated_dir, igc_with_img, ortho):
    igccol = IgcArray([], False)
    igccol.add_igc(igc_with_img)
    p = L1bProj(
        igccol, ["proj1.img"], ["ref1.img"], [ortho], separate_file_per_scan=True
    )
    pool = Pool(20)
    p.proj(pool=pool)


@pytest.mark.long_test
def test_sample_1_l1b_proj(isolated_dir, test_data_latest):
    l1a_raw_att = Path(
        "/arcdata/smyth/L1A_RAW_ATT/2025/04/13/L1A_RAW_ATT_38377_20250413T105706_0713_01.h5"
    )
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1b_rad = [
        Path(
            "/arcdata/smyth/L1B_RAD/2025/04/13/ECOv002_L1B_RAD_38377_002_20250413T105854_0713_01.h5"
        )
    ]
    l1bgeo = L1bGeoProcess(
        prod_dir=Path("."),
        l1a_raw_att=l1a_raw_att,
        l1_osp_dir=l1_osp_dir,
        l1b_rad=l1b_rad,
    )
    l1bgeo.log_string_handle = io.StringIO()
    l1bgeo.determine_output_file_name()
    igccol = l1bgeo.create_igccol_initial()
    p = L1bProj(
        igccol,
        ["proj1.img"],
        ["ref1.img"],
        ["lwm1.img"],
        l1bgeo.ortho_base,
        l1bgeo.lwm,
    )
    pool = Pool(20)
    p.proj(pool=pool, include_mask=True)
