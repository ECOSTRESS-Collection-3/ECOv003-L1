from ecostress.l1b_geo_generate_kmz import L1bGeoGenerateKmz
import pickle
import pytest


# Since L1bGeoGenerateMap and L1bGeoGenerateKmz depend on L1bGeoGenerate,
# we initially developed these by saving this out and working just
# on these classes. Once we are done with the development, don't run this
# as a standard unit test. We'll instead test this by running the full end
# to end system.
@pytest.mark.skip
def test_l1b_geo_generate_kmz(isolated_dir, igc, lwm, rad_fname):
    with open(
        "/home/smyth/Local/ecostress-level1/python/l1b_geo_generate.pickle", "rb"
    ) as f:
        l1bgeo = pickle.load(f)

    l1bgeo_kmz = L1bGeoGenerateKmz(
        l1bgeo,
        rad_fname,
        "l1b_kmz_map.kmz",
        local_granule_id="L1B_KMZ_MAP_80001_001_20151024_020211_0100_01.kmz",
        thumbnail_size=[0, 1000],
    )
    l1bgeo_kmz.run()
