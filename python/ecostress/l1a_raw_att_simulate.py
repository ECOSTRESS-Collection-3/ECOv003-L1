from __future__ import annotations
import numpy as np
import h5py  # type: ignore
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split
import geocal  # type: ignore


class L1aRawAttSimulate(object):
    """This is used to generate L1A_RAW_ATT simulated data."""

    def __init__(
        self, orb: geocal.Orbit, min_time: geocal.Time, max_time: geocal.Time
    ) -> None:
        """Create a L1ARawAttSimulate to process the given orbit."""
        self.orb = orb
        self.min_time = min_time
        self.max_time = max_time

    def create_file(self, l1a_raw_att_fname: str) -> None:
        fout = h5py.File(l1a_raw_att_fname, "w")
        # For now, we have both ephemeris and attitude with same time spacing.
        # We could change that in the future if needed.
        tspace = 1.0
        tm = np.arange(
            self.min_time.j2000 - tspace, self.max_time.j2000 + tspace, tspace
        )
        pos = np.zeros((tm.shape[0], 3))
        vel = np.zeros((tm.shape[0], 3))
        quat = np.zeros((tm.shape[0], 4))
        for i, t in enumerate(tm):
            od = self.orb.orbit_data(geocal.Time.time_j2000(t))
            pos[i, :] = od.position_ci.position
            vel[i, :] = od.velocity_ci
            quat[i, :] = geocal.quaternion_to_array(od.sc_to_ci)
        g = fout.create_group("Ephemeris")
        t = g.create_dataset("time_j2000", data=tm)
        t.attrs["Units"] = "Seconds"
        t = g.create_dataset("eci_position", data=pos)
        t.attrs["Description"] = "ECI position"
        t.attrs["Units"] = "m"
        t = g.create_dataset("eci_velocity", data=vel)
        t.attrs["Description"] = "ECI velocity"
        t.attrs["Units"] = "m/s"

        g = fout.create_group("Attitude")
        t = g.create_dataset("time_j2000", data=tm)
        t.attrs["Units"] = "Seconds"
        t = g.create_dataset("quaternion", data=quat)
        t.attrs["Description"] = (
            "Attitude quaternion, goes from spacecraft to ECI. The coefficient convention used has the real part in the first column."
        )
        t.attrs["Units"] = "dimensionless"
        m = WriteStandardMetadata(
            fout,
            product_specfic_group="L1A_RAW_ATTMetadata",
            pge_name="L1A_RAW_PGE",
            orbit_based=True,
        )
        dt, tm2 = time_split(self.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm2)
        dt, tm2 = time_split(self.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm2)
        m.write()
        fout.close()


__all__ = ["L1aRawAttSimulate"]
