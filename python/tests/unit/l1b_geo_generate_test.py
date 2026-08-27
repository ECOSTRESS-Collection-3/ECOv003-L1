from ecostress.l1b_geo_generate import L1bGeoGenerate
import geocal
from datetime import timezone
from multiprocessing import Pool
import pickle
import pytest
import duckdb
import pandas as pd

# TODO
# Temp, skip this test. We have the cloud mask in here now, but we are likely
# to rework. We check this in the end-to-end-check, so we can skip this test for
# now. Should come back to fix this
@pytest.mark.skip
def test_l1b_geo_generate(isolated_dir, igc, lwm):
    # Only do 100 lines so this runs quickly as a test
    if False:
        geocal.write_shelve("igc.xml", igc)
    l1bgeo = L1bGeoGenerate(
        igc,
        lwm,
        "l1b_geo.h5",
        [
            "fake_input.h5",
        ],
        True,
        number_line=100,
        local_granule_id="ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5",
    )
    l1bgeo.run()


# Since L1bGeoGenerateMap and L1bGeoGenerateKmz depend on L1bGeoGenerate,
# we initially developed these by saving this out and working just
# on these classes. Once we are done with the development, don't run this
# as a standard unit test. We'll instead test this by running the full end
# to end system.
@pytest.mark.skip
def test_l1b_geo_generate_save(igc, lwm):
    geocal.write_shelve("igc.xml", igc)
    l1bgeo = L1bGeoGenerate(
        igc,
        lwm,
        "l1b_geo.h5",
        [
            "fake_input.h5",
        ],
        True,
        local_granule_id="ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5",
    )
    pool = Pool(20)
    l1bgeo.run(pool=pool)
    with open("l1b_geo_generate.pickle", "wb") as f:
        pickle.dump(l1bgeo, f)

# Generate an initial set of data that we can use with our end to end test
@pytest.mark.skip
def test_generate_orbit_fit_db(test_data_latest):
    fname = "/arcdata/smyth/fit_one_orbit.parquet"
    # We initially use our one fit, we should extend this to the same logic we
    # use in our strategy. But for now just use the one fit.
    res = []
    for orb in 3662, 3663, 3664:
        t = duckdb.query(f"select attitude_time_point, parm_0, parm_1, parm_2 from '{fname}' where orbit={orb}").fetchall()
        if len(t) == 0:
            continue
        att_tm, parm_0, parm_1, parm_2 = t[0]
        tm = geocal.Time.parse_time(att_tm.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"))
        res.append({"orbit" : orb,
                    "tstart" : pd.to_datetime(str(tm)),
                    "tstart_parm_0" : parm_0,
                    "tstart_parm_1" : parm_1,
                    "tstart_parm_2" : parm_2,
                    "tend" : pd.to_datetime(str(tm)),
                    "tend_parm_0" : parm_0,
                    "tend_parm_1" : parm_1,
                    "tend_parm_2" : parm_2})
    df = pd.DataFrame(res)
    df.sort_values("orbit")
    df.to_parquet(test_data_latest / "l1_osp_dir"/ "orbit_fit.parquet")
            
