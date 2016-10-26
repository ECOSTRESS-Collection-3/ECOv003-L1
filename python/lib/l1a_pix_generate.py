from geocal import *
import h5py
import shutil
from .write_standard_metadata import WriteStandardMetadata
from .misc import process_run
from .exception import VicarException
import re

class L1aPixGenerate(object):
    '''This generates a L1A pix file from the given L1A_BB and L1A_RAW
    files.'''
    def __init__(self, l1a_bb, l1a_raw, l1a_eng, l1_osp_dir, output_name,
                 output_gain_name,
                 local_granule_id = None,
                 run_config = None, log = None,
                 quiet = False):
        '''Create a L1aPixGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_bb = os.path.abspath(l1a_bb)
        self.l1a_raw = os.path.abspath(l1a_raw)
        self.l1a_eng = os.path.abspath(l1a_eng)
        self.l1_osp_dir = os.path.abspath(l1_osp_dir)
        self.output_name = output_name
        self.output_gain_name = output_gain_name
        self.local_granule_id = local_granule_id
        self.run_config = run_config
        self.log = log
        self.quiet = quiet

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
            res = process_run(["vicarb", "el1a_bbcal",
                               "inph5e=%s" % self.l1a_eng,
                               "inph5i=%s" % self.l1a_raw,
                               "inph5b=%s" % self.l1a_bb,
                               "inpupf=%s/L1A_PCF_UPF.txt" % self.l1_osp_dir],
                              out_fh = self.log, quiet = self.quiet)
        except subprocess.CalledProcessError:
            raise VicarException("VICAR call failed")
        finally:
            os.chdir(curdir)
        # Search through log output for success message, or throw an
        # exception if we don't find it
        mtch = re.search('^VICAR_RESULT-(\d+)-\[(.*)\]', res.decode('utf-8'),
                         re.MULTILINE)
        if(mtch):
            if(mtch.group(1) != "0"):
               raise VicarException(mtch.group(2))
        else:
            raise VicarException("Success result not seen in log")
        fout = h5py.File(self.output_name, "w")
        fout_gain = h5py.File(self.output_gain_name, "w")
        # Copy output from vicar into output file.
        g = fout.create_group("UncalibratedDN")
        for b in range(1, 7):
            t = g.create_dataset("b%d_image" % b,
                  data=mmap_file("el1a_run/UncalibratedDN/b%d_image.hlf" % b))
            t.attrs["Units"] = "dimensionless"
        g = fout.create_group("BlackbodyTemp")
        for temp in (325, 295):
            t = g.create_dataset("fpa_%d" % temp,
                  data=mmap_file("el1a_run/BlackbodyTemp/fpa_%d.rel" % temp))
            t.attrs["Units"] = "K"
        g = fout.create_group("BlackbodyRadiance")
        for b in range(1, 7):
            for temp in (325, 295):
                t = g.create_dataset("b%d_%d" % (b, temp),
                  data=mmap_file("el1a_run/BlackbodyRadiance/b%d_%d.rel" %
                                 (b, temp)))
                t.attrs["Units"] = "W/m^2/sr/um"
        g = fout_gain.create_group("Gain")
        g2 = fout_gain.create_group("Offset")
        for b in range(1, 6):
            t = g.create_dataset("b%d_gain" % b,
                  data=mmap_file("el1a_run/ImgRadiance/b%d_gain.rel"%b))
            t.attrs["Units"] = "W/m^2/sr/um"
            t = g2.create_dataset("b%d_offset" % b,
                  data=mmap_file("el1a_run/ImgRadiance/b%d_offset.rel"%b))
            t.attrs["Units"] = "W/m^2/sr/um"
        # Copy over metadata
        fin = h5py.File(self.l1a_raw, "r")
        m = WriteStandardMetadata(fout,
                                  product_specfic_group = "L1APIXMetadata",
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
