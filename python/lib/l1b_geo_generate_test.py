from .l1b_geo_generate import *
import geocal
from test_support import *
from multiprocessing import Pool
import pickle

def test_l1b_geo_generate(isolated_dir, igc, lwm):
    # Only do 100 lines so this runs quickly as a test
    if(False):
        geocal.write_shelve("igc.xml", igc)
    l1bgeo = L1bGeoGenerate(igc, lwm, "l1b_geo.h5", ["fake_input.h5", ], True,
                            number_line = 100,
                            local_granule_id = "ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5")
    l1bgeo.run()

# Since L1bGeoGenerateMap and L1bGeoGenerateKmz depend on L1bGeoGenerate,
# we initially developed these by saving this out and working just
# on these classes. Once we are done with the development, don't run this
# as a standard unit test. We'll instead test this by running the full end
# to end system.
#@skip
def test_l1b_geo_generate_save(igc, lwm):
    geocal.write_shelve("igc.xml", igc)
    l1bgeo = L1bGeoGenerate(igc, lwm, "l1b_geo.h5", ["fake_input.h5", ], True,
                            local_granule_id = "ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5")
    pool = Pool(20)
    l1bgeo.run(pool=pool)
    with open('l1b_geo_generate.pickle', 'wb') as f:
        pickle.dump(l1bgeo, f)
    


