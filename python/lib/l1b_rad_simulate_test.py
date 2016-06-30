from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from geocal import *
from l1b_rad_simulate import *
from multiprocessing import Pool

# Right now depend on end to end testing. May want to have a subset
# of this defined at some point
test_data = os.path.dirname(__file__) + "/../../end_to_end_testing/"

orb = read_shelve(test_data + "orbit.xml")
cam = read_shelve(test_data + "camera.xml")
tt = read_shelve(test_data + "time_table.xml")
band = 0

def fname(band):
    return "/data/smyth/AsterMosiac/calnorm_b%d.img" % band

def test_l1b_rad_simulate():
    raise SkipTest  # Don't normally run this, it takes a while and we only
                    # have the test data on pistol
    sdata = [VicarLiteRasterImage(fname(aster_band)) for aster_band in [14, 14, 12, 11, 10, 4]]
    l1b_sim = L1bRadSimulate(orb, tt, cam, sdata, raycast_resolution = 100.0)
    # Limitation of test data is that it expects to be in end_to_end_testing
    # directory because of relative paths.
    curdir = os.getcwd()
    # Bug that we seem to need to do this to force spice to be loaded before
    # we create the pool. Would like to figure out why this happens and fix this
    SpiceHelper.spice_setup()
    try:
        os.chdir(test_data)
        pool = Pool(20)
        l1b_sim.create_file("ECOSTRESS_L1B_RAD_80001_001_20150114_1024020211_0100_01.h5",
                            pool=pool)
    finally:
        os.chdir(curdir)
    



