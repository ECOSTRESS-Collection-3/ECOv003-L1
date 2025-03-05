import pytest
from ecostress.misc import (
    determine_rotated_map_igc,
    ecostress_file_name,
    time_to_file_string,
    create_igccol,
    find_orbit_file,
    find_radiance_file,
    create_igc,
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
