import numpy as np
import h5py
from ecostress.write_standard_metadata import WriteStandardMetadata
from geocal import *

class L1aRawAttSimulate(object):
    '''This is used to generate L1A_RAW_ATT simulated data.'''
    def __init__(self, orb, min_time, max_time):
        '''Create a L1ARawAttSimulate to process the given orbit.'''
        self.orb = orb
        self.min_time = min_time
        self.max_time = max_time
        
    def create_file(self, l1a_raw_att_fname):
        fout = h5py.File(l1a_raw_att_fname, "w")
        g = fout.create_group("Ephemeris")
        t = g.create_dataset("time_j2000",
                             data = np.array([-999,-999,-999], dtype = np.float64))
        t.attrs["Units"] = "Seconds"
        g = fout.create_group("Attitude")
        t = g.create_dataset("time_j2000",
                             data = np.array([-999,-999,-999], dtype = np.float64))
        t.attrs["Units"] = "Seconds"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1A_RAW_ATTMetadata",
                                  pge_name = "L1A_RAW",
                                  orbit_based = True)
        m.write()







