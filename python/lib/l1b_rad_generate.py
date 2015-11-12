from geocal import *
import h5py
import shutil

class L1bRadGenerate(object):
    '''This generates a L1B rad file from the given L1A_PIX file.'''
    def __init__(self, l1a_pix, output_name):
        '''Create a L1bRadGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_pix = l1a_pix
        self.output_name = output_name

    def run(self):
        '''Do the actual generation of data.'''
        shutil.copyfile(self.l1a_pix, self.output_name)

