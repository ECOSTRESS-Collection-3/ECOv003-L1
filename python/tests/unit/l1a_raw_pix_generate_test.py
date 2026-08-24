from ecostress.l1a_raw_pix_generate import L1aRawPixGenerate
import ecostress
import geocal
import pytest
import subprocess
import os
from pathlib import Path


@pytest.mark.long_test
def test_l1a_raw_pix_generate(isolated_dir, test_data):
    l0b = str(test_data / "L0B_80005_20150124T204251_0100_01.h5")
    obst_dir = str(test_data)
    l1_osp_dir = str(test_data / "l1_osp_dir")
    scene_file = str(test_data / "Scene_80005_20150124T204251_20150124T204533.txt")
    l1arawpix = L1aRawPixGenerate(l0b, obst_dir, l1_osp_dir, scene_file)
    l1arawpix.run()


def test_process_scene_file(test_data):
    """Process the scene file that we generated, and make sure everything is
    ok"""
    l0b = str(test_data / "L0B_80005_20150124T204251_0100_01.h5")
    obst_dir = str(test_data / "obst_dir")
    l1_osp_dir = str(test_data / "l1_osp_dir")
    scene_file = str(test_data / "Scene_80005_20150124T204251_20150124T204533.txt")
    l1arawpix = L1aRawPixGenerate(l0b, obst_dir, l1_osp_dir, scene_file)
    t = l1arawpix.process_scene_file()
    assert t[0][0] == 80005
    assert t[1][0] == 80005
    assert t[2][0] == 80005
    assert t[0][1] == 1
    assert t[1][1] == 2
    assert t[2][1] == 3
    assert t[0][2] == geocal.Time.parse_time("2015-01-24T20:42:51.000000Z")
    assert t[1][2] == geocal.Time.parse_time("2015-01-24T20:43:42.200000Z")
    assert t[2][2] == geocal.Time.parse_time("2015-01-24T20:44:34.200000Z")
    assert t[0][3] == geocal.Time.parse_time("2015-01-24T20:43:42.200000Z")
    assert t[1][3] == geocal.Time.parse_time("2015-01-24T20:44:34.200000Z")
    assert t[2][3] == geocal.Time.parse_time("2015-01-24T20:45:29.000000Z")


def test_process_scene_file2(test_data, unit_test_data):
    """Look at what was a problem scene file uncovered in the V0.30 testing"""
    l0b = str(test_data / "L0B_80005_20150124T204251_0100_01.h5")
    obst_dir = str(test_data / "obst_dir")
    l1_osp_dir = str(test_data / "l1_osp_dir")
    scene_file = str(unit_test_data / "Scene_problem.txt")
    l1arawpix = L1aRawPixGenerate(l0b, obst_dir, l1_osp_dir, scene_file)
    t = l1arawpix.process_scene_file()
    assert t[0][0] == 80005
    assert t[1][0] == 80005
    assert t[2][0] == 80005
    assert t[0][1] == 1
    assert t[1][1] == 2
    assert t[2][1] == 3
    assert t[0][2] == geocal.Time.parse_time("2015-01-24T20:42:51.000000Z")
    assert t[1][2] == geocal.Time.parse_time("2015-01-24T20:43:52.000000Z")
    assert t[2][2] == geocal.Time.parse_time("2015-01-24T20:44:51.000000Z")
    assert t[0][3] == geocal.Time.parse_time("2015-01-24T20:43:51.000000Z")
    assert t[1][3] == geocal.Time.parse_time("2015-01-24T20:44:51.000000Z")
    assert t[2][3] == geocal.Time.parse_time("2015-01-24T20:45:36.000000Z")


# Can run everything by 1) commenting out the skip markers and 2) running:
# pytest -s tests/unit/l1a_raw_pix_generate_test.py::test_hawaii_orbit_l1a_raw && pytest -n 30 tests/unit/l1a_raw_pix_generate_test.py::test_hawaii_orbit_l1a_cal && pytest -n 30 tests/unit/l1a_raw_pix_generate_test.py::test_hawaii_orbit_l1b_rad && pytest -s tests/unit/l1a_raw_pix_generate_test.py::test_hawaii_orbit_l1b_geo && pytest -s tests/unit/l1a_raw_pix_generate_test.py::test_hawaii_orbit_l1b_proj
@pytest.mark.skip
def test_hawaii_orbit_l1a_raw(end_to_end_run_dir, test_data_latest):
    """This runs a full orbit that we used when testing out geolocation.
    This contains a hawaii scene in the first scene that had poor geolocation
    in collection 2. We will use this to test out the time fixes."""
    os.environ["AFIDS_DATA"] = "/opt/afids/data"
    os.environ["AFIDS_VDEV_DATA"] = "/opt/afids/data/vdev"
    subprocess.run(
        [
            "l1a_raw_process",
            "/arcdata/smyth/L0B/2019/08/23/L0B_06415_20190823T151324_0713_02.h5",
            "/arcdata/smyth/ObstFile/",
            "/arcdata/smyth/SceneFile/2019/08/23/Scene_06415_20190823T151325_20190823T163757_20260602T010722.txt",
            str(test_data_latest / "l1_osp_dir"),
            str(end_to_end_run_dir / "l1a_raw_06415"),
        ]
    )
    # Offset for scene 1 is 90, if we want to compare to L0B
    # fin = h5py.File("/home/smyth/Local/ecostress-level1/python/end_to_end_run/l1a_raw_06415/L1A_RAW_PIX_06415_001_20190823T151326_01.h5")
    # fin2 = h5py.File("/arcdata/smyth/l0_flex_time_data.h5")
    # time_fsw = fin["/L1A_RAW_PIXMetadata/time_fsw"][:]
    # time_fsw2 = fin2["/6415/time_fsw"][:]
    # np.count_nonzero(np.abs(time_fsw2[90:90+3714] - time_fsw)) is 0


# We have 21 results from l1a_raw
@pytest.mark.skip
@pytest.mark.parametrize("index", range(21))
def test_hawaii_orbit_l1a_cal(index, end_to_end_run_dir, test_data_latest):
    """Note that this depends on the output of
    test_hawaii_orbit_l1a_raw. We can actually set this up with some
    pytest extensions (pytest-order and pytest-dependency), but we aren't
    going to be running these tests often. So we just "know" that we need
    to run one before the other"""
    l1a_bb = sorted((end_to_end_run_dir / "l1a_raw_06415").glob("ECOv003_L1A_BB_*.h5"))[
        index
    ]
    l1a_raw_pix = sorted(
        (end_to_end_run_dir / "l1a_raw_06415").glob("L1A_RAW_PIX_*.h5")
    )[index]
    prod_dir = end_to_end_run_dir / f"l1a_cal_06415/{index:03d}"
    os.environ["AFIDS_DATA"] = "/opt/afids/data"
    os.environ["AFIDS_VDEV_DATA"] = "/opt/afids/data/vdev"
    subprocess.run(
        [
            "l1a_cal_process",
            l1a_bb,
            l1a_raw_pix,
            str(test_data_latest / "l1_osp_dir"),
            prod_dir,
        ]
    )


@pytest.mark.skip
@pytest.mark.parametrize("index", range(21))
def test_hawaii_orbit_l1b_rad(index, end_to_end_run_dir, test_data_latest):
    """Note that this depends on the output of
    test_hawaii_orbit_l1a_cal. We can actually set this up with some
    pytest extensions (pytest-order and pytest-dependency), but we aren't
    going to be running these tests often. So we just "know" that we need
    to run one before the other"""
    l1a_cal_dir = sorted((end_to_end_run_dir / "l1a_cal_06415").glob("0*"))[index]
    l1a_pix = next(l1a_cal_dir.glob("ECOv003_L1A_PIX_*.h5"))
    l1a_gain = next(l1a_cal_dir.glob("L1A_RAD_GAIN_*.h5"))
    l1a_raw_att = next((end_to_end_run_dir / "l1a_raw_06415").glob("L1A_RAW_ATT_*.h5"))
    prod_dir = end_to_end_run_dir / "l1b_rad_06415"
    os.environ["AFIDS_DATA"] = "/opt/afids/data"
    os.environ["AFIDS_VDEV_DATA"] = "/opt/afids/data/vdev"
    subprocess.run(
        [
            "l1b_rad_process",
            l1a_pix,
            l1a_gain,
            l1a_raw_att,
            str(test_data_latest / "l1_osp_dir"),
            prod_dir,
        ]
    )


@pytest.mark.skip
def test_hawaii_orbit_l1b_geo(end_to_end_run_dir, test_data_latest):
    """Note that this depends on the output of
    test_hawaii_orbit_l1b_rad. We can actually set this up with some
    pytest extensions (pytest-order and pytest-dependency), but we aren't
    going to be running these tests often. So we just "know" that we need
    to run one before the other"""
    l1a_raw_att = next((end_to_end_run_dir / "l1a_raw_06415").glob("L1A_RAW_ATT_*.h5"))
    prod_dir = end_to_end_run_dir / "l1b_geo_06415"
    os.environ["AFIDS_DATA"] = "/opt/afids/data"
    os.environ["AFIDS_VDEV_DATA"] = "/opt/afids/data/vdev"
    args = [
        "l1b_geo_process",
        l1a_raw_att,
        str(test_data_latest / "l1_osp_dir"),
        prod_dir,
    ]
    args.extend(
        sorted((end_to_end_run_dir / "l1b_rad_06415").glob("ECOv003_L1B_RAD*.h5"))
    )
    subprocess.run(args)


@pytest.mark.skip
def test_hawaii_orbit_l1b_proj(end_to_end_run_dir, test_data_latest):
    """Note that this depends on the output of
    test_hawaii_orbit_l1b_geo. We can actually set this up with some
    pytest extensions (pytest-order and pytest-dependency), but we aren't
    going to be running these tests often. So we just "know" that we need
    to run one before the other"""
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1b_geo_config = ecostress.L1bGeoQaFile.l1b_geo_config(l1_osp_dir)
    if os.path.exists("/raid22/band5_VICAR"):
        ortho_base_dir = Path("/raid22")
    elif os.path.exists("/data/smyth/Landsat/band5_VICAR"):
        ortho_base_dir = Path("/data/smyth/Landsat")
    ortho_base = geocal.Landsat7Global(
        str(ortho_base_dir),
        ecostress.band_to_landsat_band(l1b_geo_config.landsat_day_band),
    )
    ortho_scale = round(60.0 / ortho_base.map_info.resolution_meter)
    mi = ortho_base.map_info.scale(ortho_scale, ortho_scale)
    l1b_geo_file = next(
        (end_to_end_run_dir / "l1b_geo_06415").glob("ECOv003_L1B_GEO_06415_001*.h5")
    )
    l1b_rad_file = next(
        (end_to_end_run_dir / "l1b_rad_06415").glob("ECOv003_L1B_RAD_06415_001*.h5")
    )
    lat = geocal.GdalRasterImage(f'HDF5:"{l1b_geo_file}"://Geolocation/latitude')
    lon = geocal.GdalRasterImage(f'HDF5:"{l1b_geo_file}"://Geolocation/longitude')
    number_subpixel = 3
    res = ecostress.Resampler(lon, lat, mi, number_subpixel)
    rad_data = geocal.GdalRasterImage(
        f'HDF5:"{l1b_rad_file}"://Radiance/radiance_{l1b_geo_config.ecostress_day_band}'
    )
    fname = end_to_end_run_dir / "l1b_geo_06415/final_proj_06415_01.img"
    fname2 = end_to_end_run_dir / "l1b_geo_06415/final_proj_06415_01.tif"
    fname3 = end_to_end_run_dir / "l1b_geo_06415/final_ref_06415_01.tif"
    res.resample_field(str(fname), rad_data, 100.0, "HALF", True)
    subprocess.run(["gdalenhance", "-equalize", fname, fname2])
    ortho_base.create_subset_file(str(fname3), "GTIFF", [], res.map_info, "-ot Int16")
