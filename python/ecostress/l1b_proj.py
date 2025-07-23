from __future__ import annotations
from ecostress_swig import fill_value_threshold, Resampler, GroundCoordinateArray  # type: ignore
import geocal  # type: ignore
from .pickle_method import *
import numpy as np
import scipy.ndimage  # type: ignore
import os
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    from multiprocessing.pool import Pool
    from .l1b_geo_qa_file import L1bGeoQaFile


class L1bProj(object):
    """This handles projecting a Igc to the surface, forming a vicar file
    that we can then match against. We can do this in parallel if you
    pass a pool in."""

    def __init__(
        self,
        igccol: geocal.IgcCollection,
        fname_list: list[str],
        ref_fname_list: list[str],
        ortho_base: list[geocal.RasterImage],
        qa_file: L1bGeoQaFile | None = None,
        number_subpixel: int = 2,
        min_number_good_scan: int = 41,
        scratch_fname: str = "initial_lat_lon.dat",
        pass_through_error: bool = False,
        separate_file_per_scan: bool = False,
    ) -> None:
        """Project igc and generate a Vicar file fname."""
        self.igccol = igccol
        self.gc_arr = list()
        self.qa_file = qa_file
        self.ortho_base = ortho_base
        self.ref_fname_list = ref_fname_list
        self.fname_list = fname_list
        self.scratch_fname = scratch_fname
        self.separate_file_per_scan = separate_file_per_scan
        self.number_subpixel = number_subpixel
        self.pass_through_error = pass_through_error
        self.min_number_good_scan = min_number_good_scan

        # Want to scale to roughly 60 meters. Much of the landsat data is
        # at higher resolution, but ecostress is close to 70 meter pixel so
        # want data to roughly match
        self.ortho_scale = [
            round(60.0 / b.map_info.resolution_meter) for b in self.ortho_base
        ]
        for i in range(self.igccol.number_image):
            self.gc_arr.append(
                GroundCoordinateArray(self.igccol.image_ground_connection(i))
            )

    def scratch_file(self, create: bool = False) -> np.memmap:
        """Open/Create the scratch file we use in our lat/lon calculation."""
        mode = "w+" if create else "r+"
        return np.memmap(  # type:ignore[call-overload]
            self.scratch_fname,
            dtype="f8",
            mode=mode,
            shape=(
                self.igccol.number_image,
                self.igccol.image_ground_connection(0).number_line,
                self.igccol.image_ground_connection(0).number_sample,
                2,
            ),
        )

    def resample_data(self, igc_ind: int) -> bool:
        try:
            with logger.catch(reraise=True):
                mi = self.ortho_base[igc_ind].map_info.scale(
                    self.ortho_scale[igc_ind], self.ortho_scale[igc_ind]
                )
                f = self.scratch_file()
                lat: np.ndarray | None = f[igc_ind, :, :, 0]
                lon: np.ndarray | None = f[igc_ind, :, :, 1]
                if lat is None or lon is None:
                    raise RuntimeError(
                        "This can't happen, but make mypy happy by checking"
                    )
                # Handle case where we have no good data
                if np.count_nonzero(lat > -1000) == 0:
                    return False

                # This is bilinear interpolation
                lat = scipy.ndimage.interpolation.zoom(
                    lat, self.number_subpixel, order=1
                )
                # Detect the dateline. -200 is just to filter out any fill data,
                # is -180 with a bit of pad
                if np.any(lon > 170) and np.any(np.logical_and(lon > -200, lon < -170)):
                    raise RuntimeError("Don't currently handle crossing the date line")
                lon = scipy.ndimage.interpolation.zoom(
                    lon, self.number_subpixel, order=1
                )
                # Resample data to project to surface
                res = Resampler(lon, lat, mi, self.number_subpixel)
                ras = self.igccol.image_ground_connection(igc_ind).image
                logger.info("Starting resample for %s" % self.igccol.title(igc_ind))
                if self.separate_file_per_scan:
                    igc = self.igccol.image_ground_connection(igc_ind)
                    nlscan = igc.number_line_scan
                    for i in range(igc.number_scan):
                        s = slice(
                            i * nlscan * self.number_subpixel,
                            (i + 1) * nlscan * self.number_subpixel,
                        )
                        res_sub = Resampler(
                            lon[s, :],
                            lat[s, :],
                            res.map_info,
                            self.number_subpixel,
                            True,
                        )
                        ras_sub = geocal.SubRasterImage(
                            ras, i * nlscan, 0, nlscan, ras.number_sample
                        )
                        ras = self.igccol.image_ground_connection(igc_ind).image
                        b, ext = os.path.splitext(self.fname_list[igc_ind])
                        fn = b + "_%02d" % i + ext
                        res_sub.resample_field(fn, ras_sub, 1.0, "HALF", True)
                # Don't need this anymore, and the data is large. So free it
                lat = None
                lon = None
                res.resample_field(self.fname_list[igc_ind], ras, 1.0, "HALF", True)
                logger.info("Done with resample for %s" % self.igccol.title(igc_ind))
                logger.info(
                    "Starting reference image for %s" % self.igccol.title(igc_ind)
                )
                ortho = self.ortho_base[igc_ind]
                ortho.create_subset_file(
                    self.ref_fname_list[igc_ind], "VICAR", [], res.map_info, "-ot Int16"
                )
                #                                     "-ot Int16", 0 True)
                logger.info(
                    "Done with reference image for %s" % self.igccol.title(igc_ind)
                )
                return True
        except Exception:
            if not self.pass_through_error:
                raise
            logger.warning(
                f"Exception occurred while projecting {self.igccol.title(igc_ind)}"
            )
            if self.qa_file is not None:
                self.qa_file.encountered_exception = True
            return False

    def proj_scan(self, it: tuple[int, int]) -> bool:
        igc_ind, scan_index = it
        igc = self.igccol.image_ground_connection(igc_ind)
        start_line, end_line = igc.scan_index_to_line(scan_index)
        nlinescan = igc.number_line_scan
        rad = geocal.SubRasterImage(
            igc.image, start_line, 0, nlinescan, igc.image.number_sample
        )
        d = rad.read_all()
        f = self.scratch_file()
        if np.all(d <= fill_value_threshold):
            f[igc_ind, start_line:end_line, :, :] = -1e99
        else:
            t = self.gc_arr[igc_ind].ground_coor_scan_arr(start_line)
            f[igc_ind, start_line:end_line, :, :] = t[:, :, 0, 0, 0:2]
        logger.info("Done with [%d, %d, %d]" % (igc_ind, start_line, end_line))
        return True

    def proj(self, pool: Pool | None = None) -> list[bool]:
        # Create file, but then close. We reopen in each process. Without
        # this, numpy seems to create some sort of lock where only one
        # process acts at a time.
        self.scratch_file(create=True)
        # Get lat/lon. We do this in parallel, processing each scan index of
        # each scene.
        it = []
        for i in range(self.igccol.number_image):
            igc = self.igccol.image_ground_connection(i)
            if igc.number_good_scan < self.min_number_good_scan:
                logger.info(
                    "%s has only %d good scans. We require a minimum of %d, so skipping"
                    % (
                        self.igccol.title(i),
                        igc.number_good_scan,
                        self.min_number_good_scan,
                    )
                )
                self.scratch_file()[i, :, :, :] = -9999.0
            elif igc.crosses_dateline:
                logger.info(
                    "%s crosses the date line. We don't currently handle this, so skipping"
                    % self.igccol.title(i)
                )
                self.scratch_file()[i, :, :, :] = -9999.0
            else:
                for j in range(igc.number_scan):
                    it.append((i, j))
        if pool is None:
            list(map(self.proj_scan, it))
        else:
            pool.map(self.proj_scan, it)

        # Now resample data, and also resample orthobase to the same
        # map projection.
        it2 = list(range(self.igccol.number_image))
        # Seem to run into trouble doing this in parallel, I think the
        # memory use is high enough that it causes problems. May look
        # to reduce resample_data memory use somehow. This step is quick
        # enough that this probably isn't much of an actual problem in
        # practice
        return list(map(self.resample_data, it2))
        # if(pool is None):
        #    list(map(self.resample_data, it))
        # else:
        #    pool.map(self.resample_data, it)


__all__ = ["L1bProj"]
