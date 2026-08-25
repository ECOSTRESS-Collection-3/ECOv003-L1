import pytest
from ecostress import (
    determine_rotated_map_igc,
    ecostress_file_name,
    time_to_file_string,
    create_igccol,
    find_orbit_file,
    find_radiance_file,
    create_igc,
    create_orbit_raw,
    create_time_table_fix,
    L1bGeoQaFile
)
from geocal import Time, ImageCoordinate, cib01_mapinfo


# Depends on data local to eco-scf2, so don't normally run
@pytest.mark.skip
def test_find_radiance_file():
    """Test searching for a radiance file"""
    print(find_radiance_file(468, 7))


# Depends on data local to eco-scf2, so don't normally run
@pytest.mark.skip
def test_find_orbit_file():
    """Test searching for a radiance file"""
    print(find_orbit_file(468))


# Depends on data local to eco-scf2, so don't normally run
@pytest.mark.skip
def test_create_igc(test_data):
    """Test create_igc function."""
    print(
        create_igc(
            find_radiance_file(468, 7), find_orbit_file(468), test_data + "l1_osp_dir"
        )
    )


# Depends on data local to eco-scf2, so don't normally run
@pytest.mark.skip
def test_create_igccol():
    print(create_igccol(468, 7))


def test_time_to_file_string():
    """Test conversion of acquisition time to data and time."""
    t = Time.parse_time("2015-01-24T14:43:18.819553Z")
    assert time_to_file_string(t) == "20150124T144318"


def test_ecostress_file_name():
    """Test generation of ecostress file name."""
    t = Time.parse_time("2015-01-24T14:43:18.819553Z")
    assert (
        ecostress_file_name("L1B_RAD", 80001, 1, t)
        == "ECOSTRESS_L1B_RAD_80001_001_20150124T144318_0100_01.h5"
    )
    assert (
        ecostress_file_name("L1B_RAD", 80001, 1, t, collection_label="ECOv002")
        == "ECOv002_L1B_RAD_80001_001_20150124T144318_0100_01.h5"
    )
    # Build ID removed in collection 3
    assert (
        ecostress_file_name("L1B_RAD", 80001, 1, t, collection_label="ECOv003")
        == "ECOv003_L1B_RAD_80001_001_20150124T144318_01.h5"
    )


def test_determine_rotated_map_igc(igc_with_img):
    mi = cib01_mapinfo(70.0)
    mi2 = determine_rotated_map_igc(igc_with_img, mi)
    gc1 = igc_with_img.ground_coordinate(
        ImageCoordinate(0, igc_with_img.number_sample / 2)
    )
    gc2 = igc_with_img.ground_coordinate(
        ImageCoordinate(igc_with_img.number_line - 1, igc_with_img.number_sample / 2)
    )
    x1, y1 = mi2.coordinate(gc1)
    x2, y2 = mi2.coordinate(gc2)
    assert x1 == pytest.approx(x2)
    assert mi2.resolution_meter == pytest.approx(70.0, abs=1e-2)


def create_orbit_raw_(test_data_latest):
    orb = create_orbit_raw(
        test_data_latest / "L1A_RAW_ATT_05675_20190706T224819_0601_02.h5",
        test_data_latest / "l1_osp_dir",
    )
    print(orb)

def test_create_time_table_fix(test_data_latest):
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    l1b_geo_config = L1bGeoQaFile.l1b_geo_config(l1_osp_dir)
    tt1 = create_time_table_fix("/home/smyth/Local/ecostress-level1/python/end_to_end_run/l1b_rad_06415/ECOv003_L1B_RAD_06415_001_20190823T151326_01.h5", None, l1b_geo_config.mirror_rpm, l1b_geo_config.frame_time)
    tt2 = create_time_table_fix("/arcdata/smyth/L1B_RAD/2019/08/23/ECOv002_L1B_RAD_06415_001_20190823T151325_0713_04.h5", "/arcdata/smyth/L0B/2019/08/23/L0B_06415_20190823T151324_0713_02.h5", l1b_geo_config.mirror_rpm, l1b_geo_config.frame_time)
    tt3 = create_time_table_fix("/arcdata/smyth/L1B_RAD/2019/08/23/ECOv002_L1B_RAD_06415_001_20190823T151325_0713_04.h5", "/arcdata/smyth/l0_flex_time_data.h5", l1b_geo_config.mirror_rpm, l1b_geo_config.frame_time, l0b_data_fname = "/arcdata/smyth/l0_data.h5")
    tt4 = create_time_table_fix("/arcdata/smyth/rad_data.h5", "/arcdata/smyth/l0_flex_time_data.h5", l1b_geo_config.mirror_rpm, l1b_geo_config.frame_time, onum=6415, scn=1, l0b_data_fname = "/arcdata/smyth/l0_data.h5")
    # Note tt1 is slightly different (0.012 seconds). This is because L1A_RAW_PIX grabs a
    # different starting pixel because of the time difference
    print(tt1)
    print(tt2)
    print(tt3)
    print(tt4)
    
    
