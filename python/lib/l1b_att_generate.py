import geocal
import h5py
from .geo_write_standard_metadata import GeoWriteStandardMetadata
from .misc import time_split
import math
import numpy as np

class L1bAttGenerate(object):
    '''This generates the L1B att output file from the given 
    corrected orbit. 

    Note that despite the name, this is actually both attitude and ephemeris.
    '''
    def __init__(self, l1a_raw_att_fname, orbcorr, output_name,
                 tatt, teph, inlist, qa_file,
                 run_config = None, local_granule_id = None,
                 build_id = "0.30",
                 collection_label = "ECOSTRESS",
                 pge_version = "0.30",
                 correction_done = True):
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
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version
        self.inlist = inlist
        self.correction_done = correction_done
        self.qa_file = qa_file

    def run(self):
        '''Do the actual generation of data.'''
        fout = h5py.File(self.output_name, "w")
        m = GeoWriteStandardMetadata(fout,
                                  product_specfic_group = "L1GEOMetadata",
                                  proc_lev_desc = "Level 1B Geolocation Parameters",                                  
                                  pge_name="L1B_GEO",
                                  collection_label = self.collection_label,
                                  build_id = self.build_id,
                                  orbit_based = True,
                                  pge_version= self.pge_version,
                                  orbit_corrected=self.correction_done,
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
        t.attrs["Description"] = "Attitude quaternion, goes from spacecraft to ECI (J2000 Inertial Frame). The coefficient convention used has the real part in the first column. This is the reported attitude from the ISS, without correction"
        t.attrs["Units"] = "dimensionless"
        
        g = fout.create_group("Attitude")
        # Add times, being careful not to go past the edge of the orbit (since
        # this depends on both ephemeris and attitude we may have points in
        # one or the other that is outside the time range.
        have_min_time = False
        have_max_time = False
        tatt = []
        for t in self.tatt:
            if(not have_min_time and t <= self.orbcorr.min_time) :
                t = self.orbcorr.min_time
                have_min_time = True
            if(not have_max_time and t >= self.orbcorr.max_time):
                t = self.orbcorr.max_time
                have_max_time = True
            if(t >= self.orbcorr.min_time and t <= self.orbcorr.max_time):
                # We occasionally get times that are in a large gap, either
                # because there is a bad point (e.g. mangled time tag) or
                # if we start or end with a large gap in the data.
                # If that happens, just skip the time
                try:
                    od = self.orbcorr.orbit_data(t)
                    tatt.append(t)
                except RuntimeError as e:
                    if("Request time is in the middle of a large gap"
                       in str(e)):
                        pass
                    else:
                        raise
        t = g.create_dataset("time_j2000",
                             data=np.array([t.j2000 for t in tatt]))
        t.attrs["Units"] = "Seconds"
        quat = np.zeros((len(tatt), 4))
        for i, t in enumerate(tatt):
            od = self.orbcorr.orbit_data(t)
            quat[i, :] = geocal.quaternion_to_array(od.sc_to_ci)
        t = g.create_dataset("quaternion", data=quat)
        t.attrs["Description"] = "Attitude quaternion, goes from spacecraft to ECI (J2000 Inertial Frame). The coefficient convention used has the real part in the first column."
        t.attrs["Units"] = "dimensionless"

        g = fout.create_group("Uncorrected Ephemeris")
        t = g.create_dataset("time_j2000",
                             data=fraw["Ephemeris/time_j2000"])
        t.attrs["Units"] = "Seconds"
        t = g.create_dataset("eci_position", data=fraw["Ephemeris/eci_position"])
        t.attrs["Description"] = "ECI position (J2000 Inertial Frame). This is the reported position from the ISS, uncorrected."
        t.attrs["Units"] = "m"
        t = g.create_dataset("eci_velocity", data=fraw["Ephemeris/eci_velocity"])
        t.attrs["Description"] = "ECI velocity (J2000 Inertial Frame). This is the reported position from the ISS, uncorrected."
        t.attrs["Units"] = "m/s"

        g = fout.create_group("Ephemeris")
        # Add times, being careful not to past the edge of the orbit (since
        # this depends on both ephemeris and attitude we may have points in
        # one or the other that is outside the time range.
        have_min_time = False
        have_max_time = False
        teph = []
        for t in self.teph:
            if(not have_min_time and t <= self.orbcorr.min_time) :
                t = self.orbcorr.min_time
                have_min_time = True
            if(not have_max_time and t >= self.orbcorr.max_time):
                t = self.orbcorr.max_time
                have_max_time = True
            if(t >= self.orbcorr.min_time and t <= self.orbcorr.max_time):
                # We occasionally get times that are in a large gap, either
                # because there is a bad point (e.g. mangled time tag) or
                # if we start or end with a large gap in the data.
                # If that happens, just skip the time
                try:
                    od = self.orbcorr.orbit_data(t)
                    teph.append(t)
                except RuntimeError as e:
                    if("Request time is in the middle of a large gap"
                       in str(e)):
                        pass
                    else:
                        raise
        t = g.create_dataset("time_j2000", 
                             data=np.array([t.j2000 for t in teph]))
        pos = np.zeros((len(teph), 3))
        vel = np.zeros((len(teph), 3))
        for i, t in enumerate(teph):
            od = self.orbcorr.orbit_data(t)
            pos[i, :] = od.position_ci.position
            vel[i, :] = od.velocity_ci
        t = g.create_dataset("eci_position", data=pos)
        t.attrs["Description"] = "ECI position (J2000 Inertial Frame)"
        t.attrs["Units"] = "m"
        t = g.create_dataset("eci_velocity", data=vel)
        t.attrs["Description"] = "ECI velocity (J2000 Inertial Frame)"
        t.attrs["Units"] = "m/s"
        m.write()
        self.qa_file.write_standard_metadata(m)
        

__all__ = ["L1bAttGenerate"]        
