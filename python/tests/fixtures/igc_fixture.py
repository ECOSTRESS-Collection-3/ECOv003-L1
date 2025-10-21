import pytest
import geocal
import ecostress
import h5py


@pytest.fixture(scope="function")
def orb_fname(test_data):
    yield test_data / "L1A_RAW_ATT_80005_20150124T204250_0100_01.h5.expected"


@pytest.fixture(scope="function")
def rad_fname(test_data):
    yield test_data / "ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5.expected"


@pytest.fixture(scope="function")
def igc(unit_test_data, orb_fname, rad_fname):
    """Like igc_old, but a more realistic IGC. This one is already averaged
    (so 128 rows per scan)"""
    cam = geocal.read_shelve(str(unit_test_data / "camera.xml"))
    orb = geocal.HdfOrbit_Eci_TimeJ2000(
        str(orb_fname),
        "",
        "Ephemeris/time_j2000",
        "Ephemeris/eci_position",
        "Ephemeris/eci_velocity",
        "Attitude/time_j2000",
        "Attitude/quaternion",
    )
    f = h5py.File(str(rad_fname), "r")
    tmlist = f["/Time/line_start_time_j2000"][::128]
    # True here means we've already averaged the 256 lines to 128 squarish
    # lines
    vtime = geocal.Vector_Time()
    for t in tmlist:
        vtime.append(geocal.Time.time_j2000(t))
    tt = ecostress.EcostressTimeTable(vtime, True)

    # False here says it ok for SrtmDem to not have a tile. This gives support
    # for data that is over the ocean.
    dem = geocal.SrtmDem("", False)
    sm = ecostress.EcostressScanMirror()
    cam.line_order_reversed = True
    igc = ecostress.EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    yield igc


@pytest.fixture(scope="function")
def igc_with_img(igc, rad_fname):
    """Like igc, but also with raster image included"""
    igcwimg = igc
    igcwimg.image = geocal.GdalRasterImage('HDF5:"%s"://SWIR/swir_dn' % rad_fname)
    yield igcwimg


@pytest.fixture(scope="function")
def igc_hres(unit_test_data, orb_fname, rad_fname):
    """Like igc_old, but a more realistic IGC. This one is not averaged
    (so 256 rows per scan)"""
    cam = geocal.read_shelve(str(unit_test_data / "camera.xml"))
    orb = geocal.HdfOrbit_Eci_TimeJ2000(
        str(orb_fname),
        "",
        "Ephemeris/time_j2000",
        "Ephemeris/eci_position",
        "Ephemeris/eci_velocity",
        "Attitude/time_j2000",
        "Attitude/quaternion",
    )
    f = h5py.File(str(rad_fname), "r")
    tmlist = f["/Time/line_start_time_j2000"][::128]
    # False here means we've haven't averaged the 256 lines.
    vtime = geocal.Vector_Time()
    for t in tmlist:
        vtime.append(geocal.Time.time_j2000(t))
    tt = ecostress.EcostressTimeTable(vtime, False)

    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = geocal.SrtmDem("", False)
    sm = ecostress.EcostressScanMirror()
    igc = ecostress.EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    yield igc


@pytest.fixture(scope="function")
def igc_hres_latest(test_data_latest):
    """Like igc_old, but a more realistic IGC. This one is not averaged
    (so 256 rows per scan)"""
    cam = geocal.read_shelve(str(test_data_latest / "l1_osp_dir" / "camera.xml"))
    orb_fname = (
        test_data_latest / "L1A_RAW_ATT_03663_20190227T094659_01.h5.expected"
    )
    rad_fname = (
        test_data_latest
        / "ECOv003_L1B_RAD_03663_001_20190227T101222_01.h5.expected"
    )
    orb = geocal.HdfOrbit_Eci_TimeJ2000(
        str(orb_fname),
        "",
        "Ephemeris/time_j2000",
        "Ephemeris/eci_position",
        "Ephemeris/eci_velocity",
        "Attitude/time_j2000",
        "Attitude/quaternion",
    )
    f = h5py.File(str(rad_fname), "r")
    tmlist = f["/Time/line_start_time_j2000"][::128]
    # False here means we've haven't averaged the 256 lines.
    vtime = geocal.Vector_Time()
    for t in tmlist:
        vtime.append(geocal.Time.time_j2000(t))
    tt = ecostress.EcostressTimeTable(vtime, False)

    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = geocal.SrtmDem("", False)
    sm = ecostress.EcostressScanMirror()
    igc = ecostress.EcostressImageGroundConnection(orb, tt, cam, sm, dem, None)
    yield igc


@pytest.fixture(scope="function")
def igc_old(old_test_data):
    """This gives a ImageGroundConnection we can use for testing with."""
    orb = geocal.read_shelve(str(old_test_data / "orbit_old.xml"))
    cam = geocal.read_shelve(str(old_test_data / "camera_old.xml"))
    tt = geocal.read_shelve(str(old_test_data / "time_table_old.xml"))
    band = 0
    ipi = geocal.Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
    # False here says it ok for SrtmDem to not have tile. This gives support
    # for data that is over the ocean.
    dem = geocal.SrtmDem("", False)
    yield geocal.IpiImageGroundConnection(ipi, dem, None)
