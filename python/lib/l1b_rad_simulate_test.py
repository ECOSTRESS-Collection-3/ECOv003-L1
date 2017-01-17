from .l1b_rad_simulate import *
from test_support import *
from geocal import VicarLiteRasterImage, SpiceHelper
from multiprocessing import Pool

def fname(band):
    return "/data/smyth/AsterMosiac/calnorm_b%d.img" % band

@slow
def test_l1b_rad_simulate(isolated_dir, igc_old):
    raise SkipTest  # Don't normally run this, it takes a while and we only
                    # have the test data on pistol
    sdata = [VicarLiteRasterImage(fname(aster_band)) for aster_band in [14, 14, 12, 11, 10, 4]]
    l1b_sim = L1bRadSimulate(igc_old.orbit, igc_old.time_table, igc_old.camera,
                             sdata, raycast_resolution = 100.0)
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
    



