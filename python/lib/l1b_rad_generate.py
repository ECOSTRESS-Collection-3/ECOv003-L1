from geocal import *
import h5py
import shutil
from ecostress.write_standard_metadata import WriteStandardMetadata
from ecostress.misc import ecostress_radiance_scale_factor

class L1bRadGenerate(object):
    '''This generates a L1B rad file from the given L1A_PIX file.'''
    def __init__(self, l1a_pix, output_name, local_granule_id = None):
        '''Create a L1bRadGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_pix = h5py.File(l1a_pix, "r")
        self.output_name = output_name
        self.local_granule_id = local_granule_id

    def image(self, band):
        '''Generate L1B_RAD image.
        
        Right now, we just average and scale pixels. We currently use one fixed
        scaling factor to go to radiance, this will be replaced with the scaling
        from the black body data.
        
        This doesn't do anything right now for band to band registration, we just
        punt on this and assume the bands are already registered (true of our test
        data).'''
        l1a_d = self.l1a_pix["/UncalibratedPixels/pixel_data_%d" % (band + 1)][:,:]
        d = np.zeros((l1a_d.shape[0] / 2, l1a_d.shape[1]))
        d = (l1a_d[0::2, :] + l1a_d[1::2, :]) / 2.0 * \
            ecostress_radiance_scale_factor(band)
        return d
        
    def run(self):
        '''Do the actual generation of data.'''
        fout = h5py.File(self.output_name, "w")
        g = fout.create_group("Radiance")
        for b in range(6):
            t = g.create_dataset("radiance_%d" % (b + 1),
                                 data = self.image(b).astype(np.float32))
            if(b != 5):
                t.attrs["Units"] = "W/m^2/sr/um"
            else:
                t.attrs["Units"] = "dimensionless"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1B_RADMetadata",
                                  pge_name = "L1B_RAD",
                                  build_id = '0.01', pge_version='0.01',
                                  local_granule_id = self.local_granule_id)
        m.write()
