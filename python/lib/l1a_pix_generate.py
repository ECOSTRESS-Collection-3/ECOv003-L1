from geocal import *
import h5py
import shutil
from .write_standard_metadata import WriteStandardMetadata

class L1aPixGenerate(object):
    '''This generates a L1A pix file from the given L1A_BB and L1A_RAW
    files.'''
    def __init__(self, l1a_bb, l1a_raw, l1a_eng, l1_osp_dir, output_name, 
                 local_granule_id = None,
                 run_config = None, log = None):
        '''Create a L1aPixGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_bb = os.path.abspath(l1a_bb)
        self.l1a_raw = os.path.abspath(l1a_raw)
        self.l1a_eng = os.path.abspath(l1a_eng)
        self.l1_osp_dir = os.path.abspath(l1_osp_dir)
        self.output_name = output_name
        self.local_granule_id = local_granule_id
        self.run_config = run_config
        self.log = log

    def run(self):
        '''Do the actual generation of data.'''
        # Run Tom's vicar code. Note we assume we are already in the directory
        # to run in, and that Tom's code is on the TAE_PATH. This is try in
        # the way we run with the top level script
        curdir = os.getcwd()
        try:
            dirname = "./el1a_run"
            makedirs_p(dirname)
            os.chdir(dirname)
            subprocess.run(["vicarb", "el1a_bbcal",
                            "inph5e=%s" % self.l1a_eng,
                            "inph5i=%s" % self.l1a_raw,
                            "inph5b=%s" % self.l1a_bb,
                            "inpupf=%s/L1A_PCF_UPF.txt" % self.l1_osp_dir])
        finally:
            os.chdir(curdir)
        shutil.copyfile(self.l1a_raw, self.output_name)
        fin = h5py.File(self.l1a_raw, "r")
        f = h5py.File(self.output_name, "r+")
        m = WriteStandardMetadata(f, product_specfic_group = "L1APIXMetadata",
                                  pge_name="L1A_CAL_PGE",
                                  build_id = '0.10', pge_version='0.10',
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
