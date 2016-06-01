import numpy as np
import h5py
from ecostress.write_standard_metadata import WriteStandardMetadata
from ecostress.misc import ecostress_radiance_scale_factor

class L1aEngSimulate(object):
    '''This is used to generate L1A_ENG simulated data. Right now, this is just
    dummy data.'''
    def __init__(self):
        '''Create a L1APixSimulate to process the given L1B_RAD file.'''
        pass
        
    def create_file(self, l1a_eng_fname):
        fout = h5py.File(l1a_eng_fname, "w")
        g = fout.create_group("rtdBlackbodyGradients")
        t = g.create_dataset("RTD_325K",
                             data = np.array([-999,-999,-999], dtype = np.float32))
        t.attrs["Units"] = "K and XY"
        t = g.create_dataset("RTD_295K",
                             data = np.array([-999,-999,-999], dtype = np.float32))
        t.attrs["Units"] = "K and XY"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1A_ENGMetadata",
                                  pge_name = "L1A_RAW",
                                  orbit_based = True)
        m.write()







