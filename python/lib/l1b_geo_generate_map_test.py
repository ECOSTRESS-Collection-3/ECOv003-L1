from .l1b_geo_generate_map import *
import geocal
from test_support import *
from multiprocessing import Pool
import pickle

# Since L1bGeoGenerateMap and L1bGeoGenerateKmz depend on L1bGeoGenerate,
# we initially developed these by saving this out and working just
# on these classes. Once we are done with the development, don't run this
# as a standard unit test. We'll instead test this by running the full end
# to end system.
#@skip
def test_l1b_geo_generate_map(isolated_dir, igc, lwm):
    with open('/home/smyth/Local/ecostress-level1/python/l1b_geo_generate.pickle', 'rb') as f:
        l1bgeo = pickle.load(f)

    l1bgeo_map = L1bGeoGenerateMap(l1bgeo, "l1b_geo_map.h5",
                            local_granule_id = "ECOSTRESS_L1B_GEO_MAP_80001_001_20151024_020211_0100_01.h5")
    


