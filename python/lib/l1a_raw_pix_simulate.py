import numpy as np
import h5py
from .write_standard_metadata import WriteStandardMetadata

class L1aRawPixSimulate(object):
    '''This is used to generate L1A_RAW_PIX simulated data.'''
    def __init__(self, l1a_pix_fname):
        '''Create a L1APixSimulate to process the given L1A_PIX file.'''
        self.l1a_pix = h5py.File(l1a_pix_fname, "r")

    def copy_metadata(self, field):
        self.m.set(field, self.l1a_pix["/StandardMetadata/" + field].value)
        
    def create_file(self, l1a_raw_pix_fname):
        fout = h5py.File(l1a_raw_pix_fname, "w")
        g = fout.create_group("UncalibratedPixels")
        for b in range(6):
            t = g.create_dataset("pixel_data_%d" % (b+1),
                                 data = self.l1a_pix["/UncalibratedDN/b%d_image" % (b+1)], dtype="uint16")
            t.attrs["Units"] = "dimensionless"
        g = fout.create_group("Time")
        t = g.create_dataset("line_start_time_j2000",
                             data = self.l1a_pix["Time/line_start_time_j2000"])
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        # Not actually used for anything yet, but we need a value here
        enc_value = np.zeros(self.l1a_pix["Time/line_start_time_j2000"].shape,
                             dtype = np.int32)
        g = fout.create_group("FPIEencoder")
        t = g.create_dataset("EncoderValue", data=enc_value)
        t.attrs["Description"] = "Encoder values. Dummy for now"
        t.attrs["Units"] = "dimensionless"
        self.m = WriteStandardMetadata(fout,
                                       product_specfic_group = "L1A_RAW_PIXMetadata",
                                       pge_name = "L1A_RAW_PGE")
        self.copy_metadata("RangeBeginningDate")
        self.copy_metadata("RangeBeginningTime")
        self.copy_metadata("RangeEndingDate")
        self.copy_metadata("RangeEndingTime")
        self.m.write()
        fout.close()







