from geocal import *
import h5py
import shutil
from ecostress.write_standard_metadata import WriteStandardMetadata

class L1aPixGenerate(object):
    '''This generates a L1A pix file from the given L1A_BB and L1A_RAW
    files.'''
    def __init__(self, l1a_bb, l1a_raw, output_name):
        '''Create a L1aPixGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_bb = l1a_bb
        self.l1a_raw = l1a_raw
        self.output_name = output_name

    def run(self):
        '''Do the actual generation of data.'''
        shutil.copyfile(self.l1a_raw, self.output_name)
        f = h5py.File(self.output_name, "r+")
        m = WriteStandardMetadata(f)
        m.write()
