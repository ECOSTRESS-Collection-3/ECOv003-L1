from .l1b_geo_generate import *
from test_support import *
from multiprocessing import Pool


def test_l1b_geo_generate(isolated_dir, igc, lwm):
    # Only do 100 lines so this runs quickly as a test
    l1bgeo = L1bGeoGenerate(igc, lwm, "l1b_geo.h5", number_line = 100,
                            local_granule_id = "ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5")
    l1bgeo.run()



