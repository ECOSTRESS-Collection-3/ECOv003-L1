from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from write_run_config import *
from run_config import *
import os

test_data = os.path.dirname(__file__) + "/../../unit_test_data/"

def test_parse():
    '''Test creating a run config file.'''
    config = WriteRunConfig()
    config["DynamicAncillaryFileGroup", "RFIParameters"] = "/ops/LOM/ANCILLARY/RFIParameters/RFIParameters_130901_v008.h5"
    config["DynamicAncillaryFileGroup", "SpiceAntennaAzimuth"] = \
        ['/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282014_1502282059_v01.bc', 
         '/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502281929_1502282014_v01.bc', 
         '/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282059_1502282144_v01.bc'
        ]
    if(False):
        print config
    config.write_file("test.xml")
    config2 = RunConfig("test.xml")
    assert config["DynamicAncillaryFileGroup", "RFIParameters"] == \
        config2["DynamicAncillaryFileGroup", "RFIParameters"]
    assert config["DynamicAncillaryFileGroup", "SpiceAntennaAzimuth"] == \
        config2["DynamicAncillaryFileGroup", "SpiceAntennaAzimuth"]
