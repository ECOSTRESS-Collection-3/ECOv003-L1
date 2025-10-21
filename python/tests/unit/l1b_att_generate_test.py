from ecostress.l1b_att_generate import L1bAttGenerate
from ecostress.l1b_geo_qa_file import L1bGeoQaFile
from geocal import ImageCoordinate


def test_l1b_att_generate(isolated_dir, igc, orb_fname):
    tatt = [
        igc.time_table.time(ImageCoordinate(i, 0))[0] for i in range(0, 44 * 128, 128)
    ]
    teph = tatt
    qa_file = L1bGeoQaFile(
        "l1b_qa.h5",
        "fake.log",
        local_granule_id="ECOSTRESS_L1B_GEO_QA_80001_001_20151024_020211_0100_01.h5",
    )
    l1batt = L1bAttGenerate(
        orb_fname,
        igc.orbit,
        "l1b_att.h5",
        tatt,
        teph,
        [],
        qa_file,
        local_granule_id="ECOSTRESS_L1B_ATT_80001_001_20151024_020211_0100_01.h5",
    )
    l1batt.run()
