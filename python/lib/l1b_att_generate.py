from geocal import *
import h5py
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split

class L1bAttGenerate(object):
    '''This generates the L1B att output file from the given 
    ImageGroundConnection. This should have already had the orbit updated.

    Note that despite the name, this is actually both attitude and ephemeris.
    '''
    def __init__(self, igc, output_name, run_config = None,
                 local_granule_id = None):
        '''Create a L1bAttGenerate with the given ImageGroundConnection
        and output file name. To actually generate, execute the 'run'
        command.

        You can pass the run_config in which is used to fill in some of the 
        metadata. Without this, we skip that metadata and just have fill data.
        This is useful for testing, but for production you'll always want to 
        have the run config available.'''
        self.igc = igc
        self.output_name = output_name
        self.run_config = run_config
        self.local_granule_id = local_granule_id

    def sample_data(self):
        '''Return the sampled data.'''
        # We may want to get this from somewhere, but for now just hardcode
        # this
        tt = self.igc.ipi.time_table
        orb = self.igc.ipi.orbit
        rate = 1.181
        tstart = tt.min_time
        tend = tt.max_time
        npt = int(ceil((tend-tstart) / rate))
        tm = [tstart + i * rate for i in range(npt + 1)]
        tj2000 = [t.j2000 for t in tm]
        pos = np.array([orb.position_ci(t).position for t in tm])
        vel = np.array([orb.orbit_data(t).velocity_ci for t in tm])
        att = np.array([quaternion_to_array(orb.orbit_data(t).sc_to_ci) 
                        for t in tm])
        return tj2000, pos, vel, att

    def run(self):
        '''Do the actual generation of data.'''
        fout = h5py.File(self.output_name, "w")
        m = WriteStandardMetadata(fout, "L1GEOMetadata",
                                  pge_name="L1B_GEO",
                                  build_id = '0.01', pge_version='0.01',
                                  local_granule_id = self.local_granule_id)
        
        dt, tm = time_split(self.igc.ipi.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.igc.ipi.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm)
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
        g = fout.create_group("L1bAtt")
        tj2000, posd, veld, attd = self.sample_data()
        tm = g.create_dataset("time", data=tj2000, dtype="f8")
        pos = g.create_dataset("position", data=posd, dtype="f8")
        vel = g.create_dataset("velocity", data=veld, dtype="f8")
        att = g.create_dataset("attitude_quaternion", data=attd, dtype="f8")
        tm.attrs["Description"] = "J2000 time"
        tm.attrs["Units"] = "second"
        pos.attrs["Description"] = "ECI position"
        pos.attrs["Units"] = "meter"
        vel.attrs["Description"] = "ECI velocity"
        vel.attrs["Units"] = "meter/second"
        att.attrs["Description"] = "Attitude quaternion. This gives orientation of the spacecraft with the ECI coordinate system."
        att.attrs["Units"] = "dimensionless"
        m.write()
