# This defines fixtures that gives the paths to various directories with
# test data

import os
import pytest
from pathlib import Path


@pytest.fixture(scope="function")
def unit_test_data():
    """Return the unit test directory"""
    yield Path(os.path.dirname(__file__)).parent.parent.parent / "unit_test_data"


@pytest.fixture(scope="function")
def aster_mosaic_dir():
    dir = "/project/ancillary/ASTER/CAMosaic/"
    if not os.path.exists(dir):
        # Location on pistol
        dir = "/bigdata/smyth/AsterMosaic"
    if not os.path.exists(dir):
        pytest.skip("Couldn't find ASTER mosaic data")
    return Path(dir)


# Changed test data in 6.00. For backwards testing, just use the 5.00
# version of these files, it is sufficient for testing
@pytest.fixture(scope="function")
def test_data():
    """Determine the directory with the test data."""
    if "end_to_end_test_data" in os.environ:
        tdata = Path(os.environ["end_to_end_test_data"]) / "5.00"
    else:
        # Location on eco-scf
        tdata = Path("/project/test/ASTER/EndToEndTest/5.00")
        if not os.path.exists(tdata):
            # Location on pistol
            tdata = Path("/data/smyth/ecostress-test-data/5.00")
        if not os.path.exists(tdata):
            # Location on pistol
            tdata = Path("/ldata/smyth/ecostress-test-data/5.00")
        if not os.path.exists(tdata):
            pytest.skip("Don't have ecostress-test-data, so skipping test")
    if os.path.exists(tdata):
        yield tdata
    else:
        pytest.skip("Don't have ecostress-test-data, so skipping test")


@pytest.fixture(scope="function")
def test_data_latest():
    """Determine the directory with the test data."""
    if "end_to_end_test_data" in os.environ:
        tdata = Path(os.environ["end_to_end_test_data"]) / "latest"
    else:
        # Location on eco-scf
        tdata = Path("/project/test/ASTER/EndToEndTest/latest")
        if not os.path.exists(tdata):
            # Location on pistol
            tdata = Path("/data/smyth/ecostress-test-data/latest")
        if not os.path.exists(tdata):
            # Location on pistol
            tdata = Path("/ldata/smyth/ecostress-test-data/latest")
        if not os.path.exists(tdata):
            pytest.skip("Don't have ecostress-test-data, so skipping test")
    if os.path.exists(tdata):
        yield tdata
    else:
        pytest.skip("Don't have ecostress-test-data, so skipping test")


@pytest.fixture(scope="function")
def old_test_data():
    return Path(os.path.dirname(__file__)).parent.parent.parent / "end_to_end_testing"


@pytest.fixture(scope="function")
def vicar_path():
    """Add vicar_pdf to TAE_PATH"""
    original_tae_path = os.environ["TAE_PATH"]
    os.environ["TAE_PATH"] = (
        f"{Path(os.path.dirname(__file__)).parent.parent.parent / 'vicar_pdf'}:{original_tae_path}"
    )
    yield
    os.environ["TAE_PATH"] = original_tae_path


@pytest.fixture(scope="function")
def dn_fname(test_data):
    yield test_data / "ECOSTRESS_L1A_PIX_80005_001_20150124T204250_02.h5.expected"


@pytest.fixture(scope="function")
def gain_fname(test_data):
    yield test_data / "L1A_RAD_GAIN_80005_001_20150124T204250_02.h5.expected"


@pytest.fixture(scope="function")
def dn_latest_fname(test_data_latest):
    yield (
        test_data_latest
        / "ECOv003_L1A_PIX_03663_001_20190227T101222_02.h5.expected"
    )


@pytest.fixture(scope="function")
def gain_latest_fname(test_data_latest):
    yield (
        test_data_latest / "L1A_RAD_GAIN_03663_001_20190227T101222_02.h5.expected"
    )
