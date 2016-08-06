from geocal import *
import h5py
import shutil
from .write_standard_metadata import WriteStandardMetadata

class L1aPixGenerate(object):
    '''This generates a L1A pix file from the given L1A_BB and L1A_RAW
    files.'''
    def __init__(self, l1a_bb, l1a_raw, output_name, local_granule_id = None,
                 run_config = None):
        '''Create a L1aPixGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_bb = l1a_bb
        self.l1a_raw = l1a_raw
        self.output_name = output_name
        self.local_granule_id = local_granule_id
        self.run_config = run_config

    def run(self):
        '''Do the actual generation of data.'''
        shutil.copyfile(self.l1a_raw, self.output_name)
        fin = h5py.File(self.l1a_raw, "r")
        f = h5py.File(self.output_name, "r+")
        m = WriteStandardMetadata(f, product_specfic_group = "L1APIXMetadata",
                                  pge_name="L1A_CAL",
                                  build_id = '0.01', pge_version='0.01',
                                  local_granule_id = self.local_granule_id)
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
        m.set("RangeBeginningDate",
              fin["/StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime",
              fin["/StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate",
              fin["/StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime",
              fin["/StandardMetadata/RangeEndingTime"][()])
        m.write()
