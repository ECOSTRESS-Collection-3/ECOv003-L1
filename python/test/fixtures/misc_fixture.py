# Fixtures that don't really fit in one of the other files.
import pytest
import os
import geocal
from ecostress import ecostress_to_aster_band


@pytest.fixture(scope="function")
def isolated_dir(tmpdir):
    """This is a fixture that creates a temporary directory, and uses this
    while running a unit tests. Useful for tests that write out a test file
    and then try to read it.

    This fixture changes into the temporary directory, and at the end of
    the test it changes back to the current directory.

    Note that this uses the fixture tmpdir, which keeps around the last few
    temporary directories (cleaning up after a fixed number are generated).
    So if a test fails, you can look at the output at the location of tmpdir,
    e.g. /tmp/pytest-of-smyth
    """
    curdir = os.getcwd()
    try:
        tmpdir.chdir()
        yield curdir
    finally:
        os.chdir(curdir)


@pytest.fixture(scope="function")
def lwm():
    """Determine location of SRTM LWM and initialize object for that."""
    if os.path.exists("/raid25/SRTM_2014_update/srtm_v3_lwm"):
        srtm_lwm_dir = "/raid25/SRTM_2014_update/srtm_v3_lwm"
    elif os.path.exists("/project/ancillary/SRTM/srtm_v3_lwm"):
        srtm_lwm_dir = "/project/ancillary/SRTM/srtm_v3_lwm"
    else:
        pytest.skip("Couldn't find SRTM LWM")
    yield geocal.SrtmLwmData(srtm_lwm_dir, False)


@pytest.fixture(scope="function")
def aster_mosaic_surface_data(aster_mosaic_dir):
    sdata = [
        geocal.VicarLiteRasterImage(
            str(aster_mosaic_dir / f"calnorm_b{b}.img"),
            1,
            geocal.VicarLiteFile.READ,
            1000,
            1000,
        )
        for b in ecostress_to_aster_band()
    ]
    yield sdata


@pytest.fixture(scope="function")
def ortho():
    dir = "/project/ancillary/LANDSAT"
    if not os.path.exists(dir):
        # Location on pistol
        dir = "/raid22"
    if not os.path.exists(dir):
        pytest.skip("Couldn't find LANDSAT data")
    return geocal.Landsat7Global(dir, geocal.Landsat7Global.BAND5)
