# Fixtures that don't really fit in one of the other files.
import pytest
import os
import geocal

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
    '''Determine location of SRTM LWM and initialize object for that.'''
    if(os.path.exists("/raid25/SRTM_2014_update/srtm_v3_lwm")):
        srtm_lwm_dir = "/raid25/SRTM_2014_update/srtm_v3_lwm"
    elif(os.path.exists("/project/ancillary/SRTM/srtm_v3_lwm")):
        srtm_lwm_dir = "/project/ancillary/SRTM/srtm_v3_lwm"
    else:
        raise RuntimeError("Couldn't find SRTM LWM")
    yield geocal.SrtmLwmData(srtm_lwm_dir,False)
        
        
