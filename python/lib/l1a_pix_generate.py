import geocal
import h5py
import shutil
from .write_standard_metadata import WriteStandardMetadata
from .misc import process_run
from .exception import VicarRunException
import re
import os
import subprocess

class L1aPixGenerate(object):
    '''This generates a L1A pix file from the given L1A_BB and L1A_RAW
    files.'''
    def __init__(self, l1a_bb, l1a_raw, l1_osp_dir, output_name,
                 output_gain_name,
                 local_granule_id = None,
                 run_config = None, log = None,
                 quiet = False, build_id = "0.30",
                 pge_version = "0.30",
                 file_version = "01"):
        '''Create a L1aPixGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_bb = os.path.abspath(l1a_bb)
        self.l1a_raw = os.path.abspath(l1a_raw)
        self.l1_osp_dir = os.path.abspath(l1_osp_dir)
        self.output_name = output_name
        self.output_gain_name = output_gain_name
        self.local_granule_id = local_granule_id
        self.run_config = run_config
        self.log = log
        self.quiet = quiet
        self.build_id = build_id
        self.pge_version = pge_version
        self.file_version = file_version

    def _create_dir(self):
        i = 1
        done = False
        while not done:
            try:
                dirname = "./el1a_run_%03d" % i
                os.makedirs(dirname)
                done = True
            except OSError:
                i += 1
        return dirname
    
    def run(self):
        '''Do the actual generation of data.'''
        # Run Tom's vicar code. Note we assume we are already in the directory
        # to run in, and that Tom's code is on the TAE_PATH. This is try in
        # the way we run with the top level script
        curdir = os.getcwd()
        try:
            dirname = self._create_dir()
            os.chdir(dirname)
            res = process_run(["vicarb", "el1a_bbcal",
                               "inph5i=%s" % self.l1a_raw,
                               "inph5b=%s" % self.l1a_bb,
                               "inpupf=%s/L1A_PCF_UPF.txt" % self.l1_osp_dir,
                               "pcount=%s" % self.file_version],
                              out_fh = self.log, quiet = self.quiet)
        except subprocess.CalledProcessError:
            raise VicarRunException("VICAR call failed")
        finally:
            os.chdir(curdir)
        # Search through log output for success message, or throw an
        # exception if we don't find it
        mtch = re.search('^VICAR_RESULT-(\d+)-\[(.*)\]', res.decode('utf-8'),
                         re.MULTILINE)
        if(mtch):
            if(mtch.group(1) != "0"):
               raise VicarRunException(mtch.group(2))
        else:
            raise VicarRunException("Success result not seen in log")
        fout = h5py.File(self.output_name, "w")
        fout_gain = h5py.File(self.output_gain_name, "w")
        # Copy output from vicar into output file.
        g = fout.create_group("UncalibratedDN")
        t = g.create_dataset("b1_image",
                  data=geocal.mmap_file("%s/ImgRadiance/b1_dcc.hlf" % dirname))
        t.attrs["Units"] = "dimensionless"
        for b in range(2, 7):
            t = g.create_dataset("b%d_image" % b,
                  data=geocal.mmap_file("%s/UncalibratedDN/b%d_image.hlf" %
                                 (dirname, b)))
            t.attrs["Units"] = "dimensionless"
        g = fout.create_group("BlackbodyTemp")
        for temp in (325, 295):
            t = g.create_dataset("fpa_%d" % temp,
                  data=geocal.mmap_file("%s/BlackbodyTemp/fpa_%d.rel" %
                                 (dirname, temp)))
            t.attrs["Units"] = "K"
        g = fout.create_group("BlackbodyRadiance")
        for b in range(1, 7):
            for temp in (325, 295):
                t = g.create_dataset("b%d_%d" % (b, temp),
                  data=geocal.mmap_file("%s/BlackbodyRadiance/b%d_%d.rel" %
                                 (dirname, b, temp)))
                t.attrs["Units"] = "W/m^2/sr/um"
        g = fout_gain.create_group("Gain")
        g2 = fout_gain.create_group("Offset")
        for b in range(1, 6):
            t = g.create_dataset("b%d_gain" % b,
                  data=geocal.mmap_file("%s/ImgRadiance/b%d_gain.rel" % (dirname, b+1)))
            t.attrs["Units"] = "W/m^2/sr/um"
            t = g2.create_dataset("b%d_offset" % b,
                  data=geocal.mmap_file("%s/ImgRadiance/b%d_offset.rel" %
                                 (dirname,b+1)))
            t.attrs["Units"] = "W/m^2/sr/um"
        # Copy over metadata
        fin = h5py.File(self.l1a_raw, "r")
        g = fout.create_group("Time")
        t = g.create_dataset("line_start_time_j2000",
                             data = fin["Time/line_start_time_j2000"])
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        m = WriteStandardMetadata(fout,
                                  product_specfic_group = "L1APIXMetadata",
                                  proc_lev_desc = "Level 1A Calibration Parameters",
                                  pge_name="L1A_CAL_PGE",
                                  build_id = self.build_id,
                                  pge_version= self.pge_version,
                                  local_granule_id = self.local_granule_id)
        m2 = WriteStandardMetadata(fout_gain,
                                  product_specfic_group = "L1APIXMetadata",
                                  proc_lev_desc = "Level 1A Calibration Parameters",
                                  pge_name="L1A_CAL_PGE",
                                  build_id = self.build_id,
                                  pge_version= self.pge_version,
                                  local_granule_id = self.local_granule_id)
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
            m2.process_run_config_metadata(self.run_config)
        m.set("RangeBeginningDate",
              fin["/StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime",
              fin["/StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate",
              fin["/StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime",
              fin["/StandardMetadata/RangeEndingTime"][()])
        m2.set("RangeBeginningDate",
              fin["/StandardMetadata/RangeBeginningDate"][()])
        m2.set("RangeBeginningTime",
              fin["/StandardMetadata/RangeBeginningTime"][()])
        m2.set("RangeEndingDate",
              fin["/StandardMetadata/RangeEndingDate"][()])
        m2.set("RangeEndingTime",
              fin["/StandardMetadata/RangeEndingTime"][()])
        shp = geocal.mmap_file("%s/ImgRadiance/b1_dcc.hlf" % dirname).shape
        m.set("ImageLines", shp[0])
        m.set("ImagePixels", shp[1])
        m2.set("ImageLines", shp[0])
        m2.set("ImagePixels", shp[1])
        m.set_input_pointer([self.l1a_raw, self.l1a_bb,
                             "%s/L1A_PCF_UPF.txt" % self.l1_osp_dir])
        m2.set_input_pointer([self.l1a_raw, self.l1a_bb,
                              "%s/L1A_PCF_UPF.txt" % self.l1_osp_dir])
        m.write()
        m2.write()

__all__ = ["L1aPixGenerate"]
