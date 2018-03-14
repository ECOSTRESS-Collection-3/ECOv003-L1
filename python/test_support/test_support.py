# This contains support routines for doing unit tests.
import pytest
import os
from geocal import makedirs_p, read_shelve, Ipi, SrtmDem, \
    IpiImageGroundConnection, SrtmLwmData, HdfOrbit_Eci_TimeJ2000, \
    MeasuredTimeTable, Time, ImageCoordinate, VicarLiteRasterImage, \
    VicarLiteFile, Vector_Time, GdalRasterImage, Landsat7Global
import h5py
try:
    from ecostress_swig import *
    have_swig = True
except ImportError:
    have_swig = False
    
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
def vicar_path():
    '''Add vicar_pdf to TAE_PATH'''
    original_tae_path = os.environ["TAE_PATH"]
    os.environ["TAE_PATH"] = os.path.abspath(os.path.dirname(__file__) + "/../../vicar_pdf") + ":" + original_tae_path
    yield
    os.environ["TAE_PATH"] = original_tae_path
    
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
def igc_old(old_test_data):
    '''This gives a ImageGroundConnection we can use for testing with.'''
    orb = read_shelve(old_test_data + "orbit_old.xml")
    cam = read_shelve(old_test_data + "camera_old.xml")
    tt = read_shelve(old_test_data + "time_table_old.xml")
    band = 0
    ipi = Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = SrtmDem("",False)
    yield IpiImageGroundConnection(ipi, dem, None)

@pytest.yield_fixture(scope="function")
def lwm():
    '''Determine location of SRTM LWM and initialize object for that.'''
    if(os.path.exists("/raid25/SRTM_2014_update/srtm_v3_lwm")):
        srtm_lwm_dir = "/raid25/SRTM_2014_update/srtm_v3_lwm"
    elif(os.path.exists("/project/ancillary/SRTM/srtm_v3_lwm")):
        srtm_lwm_dir = "/project/ancillary/SRTM/srtm_v3_lwm"
    else:
        raise RuntimeError("Couldn't find SRTM LWM")
    yield SrtmLwmData(srtm_lwm_dir,False)

@pytest.yield_fixture(scope="function")
def aster_mosaic_dir():
    dir = "/project/ancillary/ASTER/CAMosaic/"
    if(not os.path.exists(dir)):
        # Location on pistol
        dir = "/data/smyth/AsterMosaic/"
    if(not os.path.exists(dir)):
        raise RuntimeError("Can't find location of aster mosaic")
    yield dir

@pytest.yield_fixture(scope="function")
def ortho():
    dir = "/project/ancillary/LANDSAT/band62_VICAR"
    if(not os.path.exists(dir)):
        # Location on pistol
        dir = "/raid22/band62_VICAR"
    if(not os.path.exists(dir)):
        raise RuntimeError("Can't find location of ortho base")
    return Landsat7Global(dir, Landsat7Global.BAND62)

@pytest.yield_fixture(scope="function")
def aster_mosaic_surface_data(aster_mosaic_dir):
    sdata = [VicarLiteRasterImage(aster_mosaic_dir + "calnorm_b%d.img" % b, 1,
                                  VicarLiteFile.READ, 1000, 1000)
             for b in [4, 10, 11, 12, 14, 14]]
    yield sdata
        
@pytest.yield_fixture(scope="function")
def test_data():
    '''Determine the directory with the test data.'''
    if("end_to_end_test_data" in os.environ):
        tdata = os.environ["end_to_end_test_data"] + "/"
    else:
        # Location on eco-scf
        tdata = "/project/test/ASTER/EndToEndTest/latest/"
        if(not os.path.exists(tdata)):
            # Location on pistol
            tdata="/data/smyth/ecostress-test-data/latest/"
        if(not os.path.exists(tdata)):
            raise RuntimeError("Can't find location of end to end test data")
    yield tdata

@pytest.yield_fixture(scope="function")
def igc(unit_test_data, test_data):
    '''Like igc_old, but a more realistic IGC. This one is already averaged 
    (so 128 rows per scan)'''
    if(not have_swig):
        raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
    cam = read_shelve(unit_test_data + "camera.xml")
    orb_fname = test_data + "L1A_RAW_ATT_80005_20150124T204250_0100_01.h5.expected"
    orb = HdfOrbit_Eci_TimeJ2000(orb_fname, "", "Ephemeris/time_j2000",
                                 "Ephemeris/eci_position",
                                 "Ephemeris/eci_velocity",
                                 "Attitude/time_j2000",
                                 "Attitude/quaternion")
    rad_fname = test_data + "ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5.expected"

    f = h5py.File(rad_fname, "r")
    tmlist = f["/Time/line_start_time_j2000"][::128]
    # True here means we've already averaged the 256 lines to 128 squarish
    # lines
    vtime = Vector_Time()
    for t in tmlist:
        vtime.append(Time.time_j2000(t))
    tt = EcostressTimeTable(vtime, True)
    
    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = SrtmDem("",False)
    sm = EcostressScanMirror()
    igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    yield igc

@pytest.yield_fixture(scope="function")
def igc_with_img(igc, test_data):
    '''Like igc, but also with raster image included'''
    igcwimg = igc
    rad_fname = test_data + "ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5.expected"
    igcwimg.image = GdalRasterImage('HDF5:"%s"://SWIR/swir_dn' % rad_fname)
    yield igcwimg
    
@pytest.yield_fixture(scope="function")
def dn_fname(unit_test_data, test_data):
    yield test_data + "ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_02.h5.expected"

@pytest.yield_fixture(scope="function")
def gain_fname(unit_test_data, test_data):
    yield test_data + "L1A_RAD_GAIN_80005_001_20150124T204250_0100_02.h5.expected"
    
@pytest.yield_fixture(scope="function")
def igc_hres(unit_test_data, test_data):
    '''Like igc_old, but a more realistic IGC. This one is not averaged 
    (so 256 rows per scan)'''
    if(not have_swig):
        raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
    cam = read_shelve(unit_test_data + "camera.xml")
    orb_fname = test_data + "L1A_RAW_ATT_80005_20150124T204250_0100_01.h5.expected"
    orb = HdfOrbit_Eci_TimeJ2000(orb_fname, "", "Ephemeris/time_j2000",
                                 "Ephemeris/eci_position",
                                 "Ephemeris/eci_velocity",
                                 "Attitude/time_j2000",
                                 "Attitude/quaternion")
    rad_fname = test_data + "ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5.expected"

    f = h5py.File(rad_fname, "r")
    tmlist = f["/Time/line_start_time_j2000"][::128]
    # False here means we've haven't averaged the 256 lines.
    vtime = Vector_Time()
    for t in tmlist:
        vtime.append(Time.time_j2000(t))
    tt = EcostressTimeTable(vtime, False)
    
    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = SrtmDem("",False)
    sm = EcostressScanMirror()
    igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    yield igc
    
@pytest.yield_fixture(scope="function")
def igc_btob(unit_test_data, test_data):
    '''Like igc_hres, but using test data better suited for band to band 
    testing. We have the SWIR band for each of the bands'''
    if(not have_swig):
        raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
    cam = read_shelve(unit_test_data + "camera.xml")
    orb_fname = test_data + "band_to_band/L1A_RAW_ATT_80005_20150124T204250_0100_01.h5"
    orb = HdfOrbit_Eci_TimeJ2000(orb_fname, "", "Ephemeris/time_j2000",
                                 "Ephemeris/eci_position",
                                 "Ephemeris/eci_velocity",
                                 "Attitude/time_j2000",
                                 "Attitude/quaternion")
    rad_fname = test_data + "band_to_band/ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_01.h5"

    f = h5py.File(rad_fname, "r")
    tmlist = f["/Time/line_start_time_j2000"][::256]
    # False here means we've haven't averaged the 256 lines.
    vtime = Vector_Time()
    for t in tmlist:
        vtime.append(Time.time_j2000(t))
    tt = EcostressTimeTable(vtime, False)
    
    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = SrtmDem("",False)
    sm = EcostressScanMirror()
    igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    yield igc

slow = pytest.mark.skipif(
    not pytest.config.getoption("--run-slow"),
    reason="need --run-slow option to run"
)

# Short hand for marking as unconditional skipping. Good for tests we
# don't normally run, but might want to comment out for a specific debugging
# reason.
skip = pytest.mark.skip
