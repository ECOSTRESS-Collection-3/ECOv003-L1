from ecostress.geo_write_standard_metadata import GeoWriteStandardMetadata
import h5py


def test_write_standard_metadata(isolated_dir):
    f = h5py.File("f_metadata.h5", "w")
    m = GeoWriteStandardMetadata(
        f, local_granule_id="ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5"
    )
    m.write()
    f2 = h5py.File("f2_metadata.h5", "w")
    m2 = GeoWriteStandardMetadata(
        f2,
        orbit_corrected=False,
        local_granule_id="ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5",
    )
    m2.write()
