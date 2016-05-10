from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from write_standard_metadata import *
import h5py

def test_write_standard_metadata():
    f = h5py.File("f_metadata.h5", "w")
    m = WriteStandardMetadata(f, local_granule_id = "ECOSTRESS_L1B_GEO_80001_001_20151024_020211_0100_01.h5")
    m.write()



