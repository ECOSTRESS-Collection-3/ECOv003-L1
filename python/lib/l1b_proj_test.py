from .l1b_proj import *
from test_support import *
from multiprocessing import Pool

# Don't normally run, this takes about 1 minute with 10 processors
@slow
def test_l1b_proj(isolated_dir, igc_with_img):
    p = L1bProj(igc_with_img, "proj.img")
    pool = Pool(10)
    p.proj(pool=pool)

# Not so much as test, as notes on how to generate the orthobase to match
# against
def test_ref(isolated_dir, igc_with_img):
    p = L1bProj(igc_with_img, "proj.img")
    ortho = Landsat7Global("/raid22/band62_VICAR", Landsat7Global.BAND62)
    ortho.create_subset_file("ortho.img", "VICAR", [p.f.ground_coordinate(ImageCoordinate(0,0)), p.f.ground_coordinate(ImageCoordinate(p.f.number_line-1,p.f.number_sample-1))])
    
def test_temp(unit_test_data):
    cam = read_shelve(unit_test_data + "camera.xml")
    orb_fname = "/home/smyth/Local/ecostress-level1/end_to_end_testing/l1a_raw_run/L1A_RAW_ATT_80005_20150124T204250_0100_01.h5"
    orb = HdfOrbit_Eci_TimeJ2000(orb_fname, "", "Ephemeris/time_j2000",
                                 "Ephemeris/eci_position",
                                 "Ephemeris/eci_velocity",
                                 "Attitude/time_j2000",
                                 "Attitude/quaternion")
    rad_fname = "/home/smyth/Local/ecostress-level1/end_to_end_testing/l1b_rad_run/ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5"
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
    rad = GdalRasterImage('HDF5:"%s"://SWIR/swir_dn' % rad_fname)
    igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, rad)
    
    p = L1bProj(igc, "proj.img")
    pool = Pool(10)
    p.proj(pool=pool)
    
