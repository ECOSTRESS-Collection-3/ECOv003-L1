from ecostress.rad_write_standard_metadata import RadWriteStandardMetadata
import h5py


def test_write_standard_metadata(isolated_dir):
    f = h5py.File("f_metadata.h5", "w")
    m = RadWriteStandardMetadata(
        f, local_granule_id="ECOSTRESS_L1B_RAD_80001_001_20151024_020211_0100_01.h5"
    )
    m.write()
    f2 = h5py.File("f2_metadata.h5", "w")
    m2 = RadWriteStandardMetadata(
        f2,
        line_order_flipped=True,
        local_granule_id="ECOSTRESS_L1B_RAD_80001_001_20151024_020211_0100_01.h5",
    )
    m2.write()
