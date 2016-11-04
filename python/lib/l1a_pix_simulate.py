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
        if(band == 5):
            l1b_d = self.l1b_rad["/SWIR/swir_dn"][:,:]
        else:
            l1b_d = self.l1b_rad["/Radiance/radiance_%d" % (band + 1)][:,:]
        d = np.zeros((l1b_d.shape[0] * 2, l1b_d.shape[1]), dtype=np.uint16)
        # Note we can change this to work with the gain and offset from
        # l1a if we want a fully reversible code. But for now, we do
        # the simulate in terms of DN, so there is no scaling needed here
        d[0::2,:] = l1b_d
        d[1::2,:] = d[0::2,:]
        return d

    def copy_metadata(self, field):
        self.m.set(field, self.l1b_rad["/StandardMetadata/" + field].value)
        
    def create_file(self, l1a_pix_fname):
        fout = h5py.File(l1a_pix_fname, "w")
        g = fout.create_group("UncalibratedDN")
        for b in range(6):
            t = g.create_dataset("b%d_image" % (b + 1),
                                 data = self.image(b))
            t.attrs["Units"] = "dimensionless"
        g = fout.create_group("Time")
        l1b_d = self.l1b_rad["Time/line_start_time_j2000"][:]
        d = np.zeros((l1b_d.shape[0] * 2, ), dtype='f8')
        d[0::2] = l1b_d
        d[1::2] = l1b_d
        t = g.create_dataset("line_start_time_j2000",
                             data = d, dtype="f8")
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        self.m = WriteStandardMetadata(fout, product_specfic_group = "L1A_PIXMetadata",
                                  pge_name = "L1A_CAL_PGE")
        self.copy_metadata("RangeBeginningDate")
        self.copy_metadata("RangeBeginningTime")
        self.copy_metadata("RangeEndingDate")
        self.copy_metadata("RangeEndingTime")
        self.m.write()
        fout.close()







