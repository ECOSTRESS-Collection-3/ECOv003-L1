import numpy as np
import h5py
from ecostress.write_standard_metadata import WriteStandardMetadata

class L1aBbSimulate(object):
    '''This is used to generate L1A_BB simulated data. Right now, this is just
    dummy data.'''
    def __init__(self, l1a_pix_fname):
        '''Create a L1APixSimulate to process the given L1B_RAD file.'''
        self.l1a_pix = h5py.File(l1a_pix_fname, "r")
        
    def create_file(self, l1a_bb_fname):
        fout = h5py.File(l1a_bb_fname, "w")
        g = fout.create_group("BlackBodyPixels")
        for b in range(6):
            t = g.create_dataset("B%d_blackbody_325K" % (b+1),
                                 data = np.array([999,999,999], dtype = np.uint16))
            t.attrs["Units"] = "dimensionless"
            t = g.create_dataset("B%d_blackbody_295K" % (b+1),
                                 data = np.array([999,999,999], dtype = np.uint16))
            t.attrs["Units"] = "dimensionless"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1A_BBMetadata",
                                  pge_name = "L1A_RAW")
        m.write()







