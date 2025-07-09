from ecostress.write_standard_metadata import WriteStandardMetadata
import h5py


def test_write_standard_metadata(isolated_dir):
    f = h5py.File("f_metadata.h5", "w")
    m = WriteStandardMetadata(
        f, local_granule_id="ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5"
    )
    m.write()

def test_write_xml_standard_metadata(isolated_dir):
    m = WriteStandardMetadata(
        None, xml_file="ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.xml"
    )
    m.write()
    
