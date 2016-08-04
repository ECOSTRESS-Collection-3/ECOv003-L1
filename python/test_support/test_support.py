# This contains support routines for doing unit tests.
import pytest
import os
from geocal import makedirs_p, read_shelve, Ipi, SrtmDem, \
    IpiImageGroundConnection

@pytest.yield_fixture(scope="function")
def isolated_dir(tmpdir):
    '''This is a fixture that creates a temporary directory, and uses this
    while running a unit tests. Useful for tests that write out a test file
    and then try to read it.

    This fixture changes into the temporary directory, and at the end of
    the test it changes back to the current directory.

    Note that this uses the fixture tmpdir, which keeps around the last few
    temporary directories (cleaning up after a fixed number are generated).
    So if a test fails, you can look at the output at the location of tmpdir, 
    e.g. /tmp/pytest-of-smyth
    '''
    curdir = os.getcwd()
    try:
        tmpdir.chdir()
        yield curdir
    finally:
        os.chdir(curdir)

@pytest.yield_fixture(scope="function")
def unit_test_data():
    '''Return the unit test directory'''
    yield os.path.abspath(os.path.dirname(__file__) + "/../../unit_test_data") + "/"

@pytest.yield_fixture(scope="function")
def old_test_data():
    '''This is likely to go away, but right now we depend on some older
    test data'''
    yield os.path.abspath(os.path.dirname(__file__) + "/../../end_to_end_testing") + "/"

@pytest.yield_fixture(scope="function")
def igc(old_test_data):
    '''This gives a ImageGroundConnection we can use for testing with.'''
    orb = read_shelve(old_test_data + "orbit_old.xml")
    cam = read_shelve(old_test_data + "camera.xml")
    tt = read_shelve(old_test_data + "time_table_old.xml")
    band = 0
    ipi = Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = SrtmDem("",False)
    yield IpiImageGroundConnection(ipi, dem, None)
    
@pytest.yield_fixture(scope="function")
def test_data():
    '''Determine the directory with the test data.'''
    if("end_to_end_test_data" in os.environ):
        tdata = os.environ["end_to_end_test_data"] + "/"
    else:
        # Location on eco-scf
        tdata = "/project/ancillary/ASTER/EndToEndTest/latest/"
        if(not os.path.exists(tdata)):
            # Location on pistol
            tdata="/data/smyth/ecostress-test-data/latest/"
        if(not os.path.exists(tdata)):
            raise RuntimeError("Can't find location of end to end test data")
    yield tdata
    
slow = pytest.mark.skipif(
    not pytest.config.getoption("--run-slow"),
    reason="need --run-slow option to run"
)
