from geocal import *
import h5py
import shutil
from ecostress.write_standard_metadata import WriteStandardMetadata

class L1bRadGenerate(object):
    '''This generates a L1B rad file from the given L1A_PIX file.'''
    def __init__(self, l1a_pix, output_name, local_granule_id = None):
        '''Create a L1bRadGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_pix = l1a_pix
        self.output_name = output_name
        self.local_granule_id = local_granule_id

    def run(self):
        '''Do the actual generation of data.'''
        shutil.copyfile(self.l1a_pix, self.output_name)
        f = h5py.File(self.output_name, "r+")
        m = WriteStandardMetadata(f, product_specfic_group = "L1B_RAD",
                                  pge_name="l1b_rad",
                                  build_id = '0.01', pge_version='0.01',
                                  local_granule_id = self.local_granule_id)
        m.write()
