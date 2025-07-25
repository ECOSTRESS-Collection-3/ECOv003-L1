from __future__ import annotations
import geocal  # type: ignore
from .pickle_method import *
import h5py  # type: ignore
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split
import math
import numpy as np
import typing

if typing.TYPE_CHECKING:
    from multiprocessing.pool import Pool


class L1bRadSimulate(object):
    """This is used to generate simulated input data for the L1bGeoGenerate
    process, for use in testing.

    Note for real testing you will generally want l1a_raw_simulate, which
    includes the differences in bands, the higher resolution data, etc. But
    this simulation can be useful when working on L1bGeoGenerate to short
    circuit a lot of that."""

    def __init__(
        self,
        orbit: geocal.Orbit,
        time_table: geocal.TimeTable,
        camera: geocal.Camera,
        surface_image: list[geocal.RasterImage],
        dem: None | geocal.Dem = None,
        number_integration_step: int = 1,
        raycast_resolution: int = -1,
    ) -> None:
        """Create a L1bGeoSimulate that works with the given orbit, time
        table, camera, and surface images. surface_image should have
        one image for each band.

        The default DEM to use is the SRTM, but you can pass in a
        different DEM if desired.

        The default resolution is whatever the underlying surface
        image is at, but you can specify a different resolution. Note
        that this has a strong impact on how long the data takes to
        generate. The ASTER data is 15 meter resolution, which means
        that the 70 meter ecostress pixels takes 5 x 5 subpixels. For
        a much quicker simulation, you can set this to something like
        100 meters.
        """
        self.orbit = orbit
        self.time_table = time_table
        self.camera = camera
        self.surface_image = surface_image
        self.dem = dem
        self.number_integration_step = number_integration_step
        self.raycast_resolution = raycast_resolution
        if self.dem is None:
            # False here says we use a height of 0 for missing tiles, useful
            # for data that is partially over the ocean
            self.dem = geocal.SrtmDem("", False)

    def create_file(self, l1b_rad_fname: str, pool: None | Pool = None) -> None:
        fout = h5py.File(l1b_rad_fname, "w")
        g = fout.create_group("Radiance")
        g2 = fout.create_group("SWIR")
        for b in range(6):
            # We hold camera_band to 0 for now. We'll improve this and use actually
            # other bands in the future as we flesh out the simulation.
            if b != 5:
                t = g.create_dataset(
                    "radiance_%d" % (b + 1),
                    data=self.image(b, camera_band=0, pool=pool).astype(np.float32),
                )
                t.attrs["Units"] = "W/m^2/sr/um"
            else:
                t = g2.create_dataset(
                    "swir_dn",
                    data=self.image(b, camera_band=0, pool=pool).astype(np.uint16),
                )
                t.attrs["Units"] = "dimensionless"
        g = fout.create_group("Time")
        t = g.create_dataset(
            "line_start_time_j2000",
            data=np.array(
                [
                    self.time_table.time(geocal.ImageCoordinate(i, 0))[0].j2000
                    for i in range(self.time_table.max_line + 1)
                ]
            ),
            dtype="f8",
        )
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        m = WriteStandardMetadata(
            fout, product_specfic_group="L1B_RADMetadata", pge_name="L1B_RAD_PGE"
        )
        dt, tm = time_split(self.time_table.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.time_table.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm)
        m.write()
        fout.close()

    def image_parallel_func(self, it: tuple[int, int]) -> np.ndarray:
        """Calculate image for a subset of the data, suitable for use with a
        multiprocessor pool."""
        # Handle number_sample too large here, so we don't have to
        # have special handling elsewhere
        start_sample = it[0]
        nleft = self.igc_ray_cast.number_sample - start_sample
        number_sample = min(it[1], nleft)
        return self.igc_ray_cast.read_double(
            0, start_sample, self.igc_ray_cast.number_line, number_sample
        )

    def image(
        self, band: int, camera_band: int | None = None, pool: None | Pool = None
    ) -> np.ndarray:
        """Use raycasting to generate a image for the given band. By default the
        camera_band is the same as the band, but you can optionally set it to a
        different value.

        Note that this takes about 5 minutes over ASTER data, using 20 processors
        (at 15 meter resolution)"""
        print("Doing band %d" % (band + 1))
        if camera_band is None:
            camera_band = band
        ipi = geocal.Ipi(
            self.orbit,
            self.camera,
            camera_band,
            self.time_table.min_time,
            self.time_table.max_time,
            self.time_table,
        )
        igc = geocal.IpiImageGroundConnection(ipi, self.dem, None)
        self.igc_ray_cast = geocal.IgcSimulatedRayCaster(
            igc,
            self.surface_image[band],
            self.number_integration_step,
            self.raycast_resolution,
        )
        if pool is None:
            return self.image_parallel_func((0, self.igc_ray_cast.number_sample))
        nprocess = pool._processes  # type: ignore[attr-defined]
        n = math.floor(self.igc_ray_cast.number_sample / nprocess)
        if self.igc_ray_cast.number_sample % nprocess > 0:
            n += 1
        it = [(i, n) for i in range(0, self.igc_ray_cast.number_sample, n)]
        rv = pool.map(self.image_parallel_func, it)
        r = np.hstack(rv)
        r[r < 0] = 0
        return r


__all__ = ["L1bRadSimulate"]
