import numpy as np
import h5py
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split

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
                                  pge_name = "L1A_RAW_PGE",
                                  orbit_based = True)
        dt, tm = time_split(self.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.max_time)
        m.set("RangeEndingDate", dt) 
        m.set("RangeEndingTime", tm)
        m.write()
        fout.close()






