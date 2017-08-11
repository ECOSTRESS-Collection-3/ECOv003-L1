from geocal import *
from ecostress_swig import *
import h5py
import shutil
from .write_standard_metadata import WriteStandardMetadata
from .misc import ecostress_radiance_scale_factor

class L1bRadGenerate(object):
    '''This generates a L1B rad file from the given L1A_PIX file.'''
    def __init__(self, l1a_pix, l1a_gain, output_name, local_granule_id = None,
                 run_config = None, log = None, build_id = "0.30",
                 pge_version = "0.30"):
        '''Create a L1bRadGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.l1a_pix_fname = l1a_pix
        self.l1a_pix = h5py.File(l1a_pix, "r")
        self.l1a_gain_fname = l1a_gain
        self.output_name = output_name
        self.local_granule_id = local_granule_id
        self.run_config = run_config
        self.log = log
        self.build_id = build_id
        self.pge_version = pge_version

    def image(self, band):
        '''Generate L1B_RAD image.
        
        Right now, we just average and scale pixels. We currently use
        one fixed scaling factor to go to radiance, this will be
        replaced with the scaling from the black body data.
        
        This does not do anything right now for band to band
        registration, we just punt on this and assume the bands are
        already registered (true of our test data).'''

        rad = EcostressRadApply(self.l1a_pix_fname, self.l1a_gain_fname, band)
        d = rad.read_all_double()
        res = (d[0::2, :] + d[1::2, :]) / 2.0
        res[d[0::2, :] < -9998] = -9999
        res[d[1::2, :] < -9998] = -9999
        return res
        
    def run(self):
        '''Do the actual generation of data.'''
        fout = h5py.File(self.output_name, "w")
        g = fout.create_group("Radiance")
        for b in range(5):
            t = g.create_dataset("radiance_%d" % (b + 1),
                                 data = self.image(b).astype(np.float32))
            t.attrs["Units"] = "W/m^2/sr/um"
        g = fout.create_group("SWIR")
        t = g.create_dataset("swir_dn",
                             data = self.image(5).astype(np.uint16))
        t.attrs["Units"] = "dimensionless"
        g = fout.create_group("Time")
        t = g.create_dataset("line_start_time_j2000",
                             data = self.l1a_pix["Time/line_start_time_j2000"][0::2])
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1B_RADMetadata",
                                  pge_name = "L1B_RAD_PGE",
                                  build_id = self.build_id,
                                  pge_version= self.pge_version,
                                  local_granule_id = self.local_granule_id)
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
        m.set("RangeBeginningDate",
              self.l1a_pix["/StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime",
              self.l1a_pix["/StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate",
              self.l1a_pix["/StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime",
              self.l1a_pix["/StandardMetadata/RangeEndingTime"][()])
        m.write()
