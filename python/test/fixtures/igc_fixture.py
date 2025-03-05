from .dir_fixture import unit_test_data, test_data
import pytest
import geocal
import ecostress
import h5py

@pytest.fixture(scope="function")
def orb_fname(unit_test_data, test_data):
    yield test_data + "L1A_RAW_ATT_80005_20150124T204250_0100_01.h5.expected"

@pytest.fixture(scope="function")
def rad_fname(unit_test_data, test_data):
    yield test_data + "ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5.expected"
    
@pytest.fixture(scope="function")
def igc(unit_test_data, test_data, orb_fname, rad_fname):
    '''Like igc_old, but a more realistic IGC. This one is already averaged 
    (so 128 rows per scan)'''
    if(not have_swig):
        raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
    cam = geocal.read_shelve(unit_test_data + "camera.xml")
    orb = geocal.HdfOrbit_Eci_TimeJ2000(orb_fname, "", "Ephemeris/time_j2000",
                                        "Ephemeris/eci_position",
                                        "Ephemeris/eci_velocity",
                                        "Attitude/time_j2000",
                                        "Attitude/quaternion")
    f = h5py.File(rad_fname, "r")
    tmlist = f["/Time/line_start_time_j2000"][::128]
    # True here means we've already averaged the 256 lines to 128 squarish
    # lines
    vtime = geocal.Vector_Time()
    for t in tmlist:
        vtime.append(geocal.Time.time_j2000(t))
    tt = ecostress.EcostressTimeTable(vtime, True)
    
    # False here says it ok for SrtmDem to not have a tile. This gives support
    # for data that is over the ocean.
    dem = geocal.SrtmDem("",False)
    sm = ecostress.EcostressScanMirror()
    cam.line_order_reversed = True
    igc = ecostress.EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    yield igc

@pytest.fixture(scope="function")
def igc_with_img(igc, test_data, rad_fname):
    '''Like igc, but also with raster image included'''
    igcwimg = igc
    igcwimg.image = geocal.GdalRasterImage('HDF5:"%s"://SWIR/swir_dn' % rad_fname)
    yield igcwimg
