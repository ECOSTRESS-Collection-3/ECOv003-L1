from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from write_standard_metadata import *
import h5py

def test_write_standard_metadata():
    f = h5py.File("f_metadata.h5", "w")
    m = WriteStandardMetadata(f)
    m.write()



