from __future__ import annotations
import numpy as np
import h5py  # type: ignore
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split
from ecostress_swig import (  # type: ignore
    fill_value_threshold,
    GroundCoordinateArray,
    SimulatedRadiance,
)
import geocal  # type: ignore
import typing

if typing.TYPE_CHECKING:
    from multiprocessing.pool import Pool


class L1aPixSimulate(object):
    """This is used to generate L1A_PIX simulated data from a L1B_RAD file.
    This is the inverse of the l1b_rad_generate process."""

    def __init__(
        self,
        igc: geocal.ImageGroundConnection,
        surface_image: list[geocal.RasterImage],
        gain_fname: None | str = None,
        scale_factor: None | list[float | None] = None,
    ) -> None:
        """Create a L1APixSimulate to process the given
        EcostressImageGroundConnection.  We supply the surface map projected
        image as an array, one entry per band in the igc."""
        self.igc = igc
        self.surface_image = surface_image
        self.gain_fname = gain_fname
        self.scale_factor = scale_factor

    def image_parallel_func(self, it: tuple[int, int]) -> np.ndarray:
        """Calculate image for a subset of data."""
        return self.sim_rad.radiance_scan(it[0], it[1])

    def image(self, band: int, pool: Pool | None = None) -> np.ndarray:
        """Generate a l1a pix image for the given band."""
        print("Doing band %d" % (band + 1))
        self.igc.band = band
        # Don't bother averaging data, just use the center pixel. Since we
        # are simulated, this should be fine and is much faster.
        avg_fact = 1
        self.sim_rad = SimulatedRadiance(
            GroundCoordinateArray(self.igc), self.surface_image[band], avg_fact
        )
        it = [(i, 256) for i in range(0, self.igc.number_line, 256)]
        if pool:
            rv = pool.map(self.image_parallel_func, it)
        else:
            rv = list(map(self.image_parallel_func, it))
        r = np.vstack(rv)
        # Don't think we have any negative data, but go ahead and zero this out
        # if there is any
        r[r < 0] = 0
        if self.scale_factor is not None and self.scale_factor[band] is not None:
            r = self.scale_factor[band] * r
        # If we have a gain_fname, use that to scale the data
        if band != 0 and self.gain_fname is not None:
            f = h5py.File(self.gain_fname, "r")
            gain = f["Gain/b%d_gain" % band][:]
            offset = f["Offset/b%d_offset" % band][:]
            # Remove bad pixels in gain/offset - we only want to introduce
            # that based on the data, not on our current gain/offset
            for i in range(256):
                s = slice(i, None, 256)
                gain[s, :] = gain[s, :].max()
                offset[s, :] = offset[s, :].max()
            r = (r - offset) / gain
        # We don't record this anywhere in the HDF file that I can easily
        # find. But we want to add the dark current subtraction back in so
        # we get the original DNs out.
        # This is the average of the two blackbody values for
        # 325K and 295K. The l1a_bb_simulate.py value averages to 5. If
        # we end up changing this, we can probably come up with a better
        # way of modifying this.
        if band == 0:
            r[r > fill_value_threshold] += 5
        r = r.astype(np.int16)
        return r

    def create_file(self, l1a_pix_fname: str, pool: None | Pool = None) -> None:
        fout = h5py.File(l1a_pix_fname, "w")
        g = fout.create_group("UncalibratedDN")
        for b in range(6):
            t = g.create_dataset("b%d_image" % (b + 1), data=self.image(b, pool=pool))
            t.attrs["Units"] = "dimensionless"
        g = fout.create_group("Time")
        t = g.create_dataset(
            "line_start_time_j2000",
            data=np.array(
                [
                    self.igc.time_table.time(geocal.ImageCoordinate(i, 0))[0].j2000
                    for i in range(self.igc.time_table.max_line + 1)
                ]
            ),
            dtype="f8",
        )
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        m = WriteStandardMetadata(
            fout, product_specfic_group="L1A_PIXMetadata", pge_name="L1A_CAL_PGE"
        )
        dt, tm = time_split(self.igc.time_table.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.igc.time_table.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm)
        m.write()
        fout.close()


__all__ = ["L1aPixSimulate"]
