import numpy as np
import h5py
from .write_standard_metadata import WriteStandardMetadata

class L1aEngSimulate(object):
    '''This is used to generate L1A_ENG simulated data. Right now, this is just
    dummy data.'''
    def __init__(self, l1a_raw_att_fname):
        '''Create a L1APixSimulate to process the given L1B_RAD file.'''
        # Right now, get times from raw att file
        self.att_file = h5py.File(l1a_raw_att_fname)
        self.time_j2000 = self.att_file["/Ephemeris/time_j2000"][:]
        
    def create_file(self, l1a_eng_fname):
        fout = h5py.File(l1a_eng_fname, "w")
        g = fout.create_group("rtdBlackbodyGradients")
        data = np.zeros((self.time_j2000.shape[0], 5))
        data[:,:] = 325
        t = g.create_dataset("RTD_325K",
                             data = np.array(data, dtype = np.float32))
        t.attrs["Units"] = "K and XY"
        data[:,:] = 295
        t = g.create_dataset("RTD_295K",
                             data = np.array(data, dtype = np.float32))
        t.attrs["Units"] = "K and XY"
        t = g.create_dataset("Time_j2000", data = self.time_j2000)
        t.attrs["Units"] = "Seconds"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1A_ENGMetadata",
                                  pge_name = "L1A_RAW_PGE",
                                  orbit_based = True)
        m.set("RangeBeginningDate", self.att_file["/StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime", self.att_file["/StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate", self.att_file["/StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime", self.att_file["/StandardMetadata/RangeEndingTime"][()])
        m.write()
        fout.close()

__all__ = ["L1aEngSimulate"]




