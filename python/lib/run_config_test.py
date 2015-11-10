from nose.tools import *
from nose.plugins.skip import Skip, SkipTest
from run_config import *
import os

test_data = os.path.dirname(__file__) + "/../../unit_test_data/"

def test_parse():
    '''Test parsing a sample run config file.'''
    config = RunConfig(test_data + 
                       "SMAP_L1B_TB_SPS_RunConfig_20150228T224642376.xml")
    assert config["DynamicAncillaryFileGroup", "RFIParameters"] == "/ops/LOM/ANCILLARY/RFIParameters/RFIParameters_130901_v008.h5"
    assert config["DynamicAncillaryFileGroup", "SpiceAntennaAzimuth"] == \
        ['/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282014_1502282059_v01.bc', 
         '/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502281929_1502282014_v01.bc', 
         '/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282059_1502282144_v01.bc'
        ]

