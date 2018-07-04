import geocal
import h5py
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split
import math
import numpy as np

class L1bAttGenerate(object):
    '''This generates the L1B att output file from the given 
    corrected orbit. 

    Note that despite the name, this is actually both attitude and ephemeris.
    '''
    def __init__(self, l1a_raw_att_fname, orbcorr, output_name,
                 tatt, teph, inlist,
                 run_config = None, local_granule_id = None,
                 build_id = "0.30",
                 pge_version = "0.30"):
        '''Create a L1bAttGenerate with the given ImageGroundConnection
        and output file name. To actually generate, execute the 'run'
        command.

        You can pass the run_config in which is used to fill in some of the 
        metadata. Without this, we skip that metadata and just have fill data.
        This is useful for testing, but for production you'll always want to 
        have the run config available.'''
        self.l1a_raw_att_fname = l1a_raw_att_fname
        self.orbcorr = orbcorr
        self.output_name = output_name
        self.tatt = tatt
        self.teph = teph
        self.run_config = run_config
        self.local_granule_id = local_granule_id
        self.build_id = build_id
        self.pge_version = pge_version
        self.inlist = inlist

    def run(self):
        '''Do the actual generation of data.'''
        fout = h5py.File(self.output_name, "w")
        m = WriteStandardMetadata(fout,
                                  product_specfic_group = "L1GEOMetadata",
                                  proc_lev_desc = "Level 1B Geolocation Parameters",                                  
                                  pge_name="L1B_GEO",
                                  build_id = self.build_id,
                                  orbit_based = True,
                                  pge_version= self.pge_version,
                                  local_granule_id = self.local_granule_id)
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
        m.set("ImageLines", 0)
        m.set("ImagePixels", 0)
        dt, tm = time_split(self.orbcorr.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.orbcorr.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm)
        m.set_input_pointer(self.inlist)
        fraw = h5py.File(self.l1a_raw_att_fname, "r")

        g = fout.create_group("Uncorrected Attitude")
        t = g.create_dataset("time_j2000",
                             data=fraw["Attitude/time_j2000"])
        t.attrs["Units"] = "Seconds"
        t = g.create_dataset("quaternion", data=fraw["Attitude/quaternion"])
        t.attrs["Description"] = "Attitude quaternion, goes from spacecraft to ECI. The coefficient convention used has the real part in the first column. This is the reported attitude from the ISS, without correction"
        t.attrs["Units"] = "dimensionless"
        
        g = fout.create_group("Attitude")
        t = g.create_dataset("time_j2000",
                             data=np.array([t.j2000 for t in self.tatt]))
        t.attrs["Units"] = "Seconds"
        quat = np.zeros((len(self.tatt), 4))
        for i, t in enumerate(self.tatt):
            od = self.orbcorr.orbit_data(t)
            quat[i, :] = geocal.quaternion_to_array(od.sc_to_ci)
        t = g.create_dataset("quaternion", data=quat)
        t.attrs["Description"] = "Attitude quaternion, goes from spacecraft to ECI. The coefficient convention used has the real part in the first column."
        t.attrs["Units"] = "dimensionless"

        g = fout.create_group("Uncorrected Ephemeris")
        t = g.create_dataset("time_j2000",
                             data=fraw["Ephemeris/time_j2000"])
        t.attrs["Units"] = "Seconds"
        t = g.create_dataset("eci_position", data=fraw["Ephemeris/eci_position"])
        t.attrs["Description"] = "ECI position. This is the reported position from the ISS, uncorrected."
        t.attrs["Units"] = "m"
        t = g.create_dataset("eci_velocity", data=fraw["Ephemeris/eci_velocity"])
        t.attrs["Description"] = "ECI velocity. This is the reported position from the ISS, uncorrected."
        t.attrs["Units"] = "m/s"

        g = fout.create_group("Ephemeris")
        t = g.create_dataset("time_j2000", 
                             data=np.array([t.j2000 for t in self.teph]))
        pos = np.zeros((len(self.teph), 3))
        vel = np.zeros((len(self.teph), 3))
        for i, t in enumerate(self.teph):
            od = self.orbcorr.orbit_data(t)
            pos[i, :] = od.position_ci.position
            vel[i, :] = od.velocity_ci
        t = g.create_dataset("eci_position", data=pos)
        t.attrs["Description"] = "ECI position"
        t.attrs["Units"] = "m"
        t = g.create_dataset("eci_velocity", data=vel)
        t.attrs["Description"] = "ECI velocity"
        t.attrs["Units"] = "m/s"
        m.write()

__all__ = ["L1bAttGenerate"]        
