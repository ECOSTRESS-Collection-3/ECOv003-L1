from geocal import *
import h5py
import shutil
from ecostress.write_standard_metadata import WriteStandardMetadata

class L1aRawPixGenerate(object):
    '''This generates a L1A_RAW_PIX, L1A_BB, L1A_ENG and L1A_RAW_ATT
    files from a L0 input.'''
    def __init__(self, l0):
        '''Create a L1aRawPixGenerate to process the given L0 file. 
        To actually generate, execute the 'run' command.'''
        self.l0 = l0

    def run(self):
        '''Do the actual generation of data.'''
        return
        shutil.copyfile(self.l1a_raw, self.output_name)
        f = h5py.File(self.output_name, "r+")
        m = WriteStandardMetadata(f, product_specfic_group = "L1APIXMetadata",
                                  pge_name="L1A_CAL",
                                  build_id = '0.01', pge_version='0.01',
                                  local_granule_id = self.local_granule_id)
        m.write()
