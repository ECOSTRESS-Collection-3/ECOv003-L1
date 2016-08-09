from .misc import *
from test_support import *
from geocal import Time

def test_time_to_file_string():
    '''Test conversion of acquisition time to data and time.'''
    t = Time.parse_time("2015-01-24T14:43:18.819553Z")
    assert time_to_file_string(t) == "20150124T144318" 


def test_ecostress_file_name():
    '''Test generation of ecostress file name.'''
    t = Time.parse_time("2015-01-24T14:43:18.819553Z")
    assert ecostress_file_name("L1B_RAD", 80001, 1, t) == \
        "ECOSTRESS_L1B_RAD_80001_001_20150124T144318_0100_01.h5"
    


