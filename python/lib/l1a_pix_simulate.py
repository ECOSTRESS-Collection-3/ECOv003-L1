import numpy as np
import h5py
from .write_standard_metadata import WriteStandardMetadata
from .misc import ecostress_radiance_scale_factor

class L1aPixSimulate(object):
    '''This is used to generate L1A_PIX simulated data from a L1B_RAD file.
    This is the inverse of the l1b_rad_generate process.'''
    def __init__(self, l1b_rad_file):
        '''Create a L1APixSimulate to process the given L1B_RAD file.'''
        self.l1b_rad = h5py.File(l1b_rad_file, "r")
        
    def image(self, band):
        '''Generate a l1a pix image for the given band.'''
        l1b_d = self.l1b_rad["/Radiance/radiance_%d" % (band + 1)][:,:]
        d = np.zeros((l1b_d.shape[0] * 2, l1b_d.shape[1]), dtype=np.uint16)
        d[0::2,:] = l1b_d / ecostress_radiance_scale_factor(band)
        d[1::2,:] = d[0::2,:]
        return d

    def copy_metadata(self, field):
        self.m.set(field, self.l1b_rad["/StandardMetadata/" + field].value)
        
    def create_file(self, l1a_pix_fname):
        fout = h5py.File(l1a_pix_fname, "w")
        g = fout.create_group("UncalibratedPixels")
        for b in range(6):
            t = g.create_dataset("pixel_data_%d" % (b + 1),
                                 data = self.image(b))
            t.attrs["Units"] = "dimensionless"
        self.m = WriteStandardMetadata(fout, product_specfic_group = "L1A_PIXMetadata",
                                  pge_name = "L1A_CAL_PGE")
        self.copy_metadata("RangeBeginningDate")
        self.copy_metadata("RangeBeginningTime")
        self.copy_metadata("RangeEndingDate")
        self.copy_metadata("RangeEndingTime")
        self.m.write()
        fout.close()







