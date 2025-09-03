from __future__ import annotations
import numpy as np
import geocal  # type: ignore
from .cloud_processing import CloudProcessing
from ecostress_swig import (  # type: ignore
    EcostressTimeTable,
    GroundCoordinateArray,
    FILL_VALUE_BAD_OR_MISSING,
)
import h5py  # type: ignore
import sys
from functools import cached_property
from pathlib import Path
from loguru import logger
import os
import types
import typing

if typing.TYPE_CHECKING:
    from multiprocessing.pool import Pool


class CloudMask:
    """Depending on how the processing is done, we might calculate the
    cloud mask as different points. We wait until we need this to get
    the most accurate latitude and longitude to use in the processing.
    The cloud mask is super sensitive to the lat/lon, so we don't need
    to recalculate this as we update our Igc pointing.

    This class handles the actual calculation of the cloud mask and stores
    the results."""

    def __init__(
        self,
        radfname: str | os.PathLike,
        l1_osp_dir: str | os.PathLike,
        rad_lut_fname: str | os.PathLike | None = None,
        b11_lut_file_pattern: str | os.PathLike | None = None,
    ) -> None:
        """Initialize, passing in the l1b radiance file we use.

        By default we get the CloudProcessing parameter files from
        the L1 OSP directory, but you can optionally supply these
        (e.g., comparing against old data).
        """
        self.radfname = radfname
        self._cloud: np.ndarray | None = None
        self._cloud_conf: np.ndarray | None = None
        self.l1_osp_dir = Path(l1_osp_dir)
        self.cprocess = CloudProcessing(
            rad_lut_fname
            if rad_lut_fname is not None
            else self.l1_osp_dir / self.l1b_geo_config.rad_lut_fname,
            b11_lut_file_pattern
            if b11_lut_file_pattern is not None
            else self.l1_osp_dir / self.l1b_geo_config.b11_lut_file_pattern,
        )

    @cached_property
    def l1b_geo_config(self) -> types.ModuleType:
        try:
            sys.path.append(str(self.l1_osp_dir))
            import l1b_geo_config  # type: ignore

            return l1b_geo_config
        finally:
            sys.path.remove(str(self.l1_osp_dir))

    def _loc_parallel_func(
        self, it: tuple[int, int]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        start_line, number_line = it
        try:
            # Note res here refers to an internal cache array of gc_arr
            res = self.gc_arr.ground_coor_scan_arr(start_line, number_line)
            logger.info(f"Done with [{start_line}, {start_line + res.shape[0]}]")
        except RuntimeError:
            res = np.empty((number_line, self.igc.image.number_sample, 1, 1, 3))
            res[:] = FILL_VALUE_BAD_OR_MISSING
            logger.info(f"Skipping [{start_line}, {start_line + res.shape[0]}]")
        # Note the copy() here is very important. As an optimization,
        # ground_coor_scan_arr return a reference to an internal cache
        # variable. This array gets overwritten in the next call to
        # ground_coor_scan_arr. So we need to explicitly copy anything
        # we want to keep.
        lat = res[:, :, 0, 0, 0].copy()
        lon = res[:, :, 0, 0, 1].copy()
        height = res[:, :, 0, 0, 2].copy()
        return (lat, lon, height)

    def _fill_in(
        self,
        igc: geocal.ImageGroundConnection | None,
        lat: np.ndarray | None,
        lon: np.ndarray | None,
        height: np.ndarray | None,
        pool: None | Pool = None,
    ) -> None:
        """Calculate cloud mask, if it hasn't already been done so.
        We either take lat, lon, and height for the scene (if already available)
        or we can take an igc to calculate this.
        """
        if self._cloud is not None:
            return
        if not (
            (lat is not None and lon is not None and height is not None)
            or igc is not None
        ):
            raise RuntimeError("Need to supply either lat, lon and height or the igc")
        # TODO Add igc support
        rad_band_4 = h5py.File(self.radfname, "r")["//Radiance/radiance_4"][:, :]
        if igc is not None:
            tt = igc.time_table
        else:
            tt = EcostressTimeTable(
                str(self.radfname),
                self.l1b_geo_config.mirror_rpm,
                self.l1b_geo_config.frame_time,
            )
        if igc is not None and hasattr(igc, "start_sample"):
            # Subset if we are working with subsetted data
            rad_band_4 = rad_band_4[
                :,
                igc.start_sample : igc.start_sample + igc.number_sample,
            ]
        if lat is None or lon is None or height is None:
            assert igc is not None
            self.gc_arr = GroundCoordinateArray(igc)
            self.igc = igc
            it = []
            for i in range(self.igc.number_scan):
                ls, le = self.igc.scan_index_to_line(i)
                it.append((ls, le - ls))
            if pool is None:
                r = list(map(self._loc_parallel_func, it))
            else:
                r = pool.map(self._loc_parallel_func, it)
            lat = np.vstack([rv[0] for rv in r])
            lon = np.vstack([rv[1] for rv in r])
            height = np.vstack([rv[2] for rv in r])
        assert lat is not None and lon is not None and height is not None
        self._cloud, self._cloud_conf = self.cprocess.process_cloud(
            rad_band_4, lat, lon, height, tt.min_time + (tt.max_time - tt.min_time) / 2
        )

    def cloud_mask(
        self,
        igc: geocal.ImageGroundConnection | None = None,
        lat: np.ndarray | None = None,
        lon: np.ndarray | None = None,
        height: np.ndarray | None = None,
        pool: None | Pool = None,
    ) -> np.ndarray:
        """Return the cloud mask (calculating if needed). Depending
        on where we are called, the lat, lon, and height for the scene
        might already be available. If it is, we can use this directly.
        Otherwise the igc should be passed in and we calculate this if needed."""
        self._fill_in(igc, lat, lon, height, pool)
        assert self._cloud is not None
        return self._cloud

    def cloud_confidence(
        self,
        igc: geocal.ImageGroundConnection | None = None,
        lat: np.ndarray | None = None,
        lon: np.ndarray | None = None,
        height: np.ndarray | None = None,
        pool: None | Pool = None,
    ) -> np.ndarray:
        """Return the cloud mask confidence (calculating if needed). Depending
        on where we are called, the lat, lon, and height for the scene
        might already be available. If it is, we can use this directly.
        Otherwise the igc should be passed in and we calculate this if needed."""
        self._fill_in(igc, lat, lon, height, pool)
        assert self._cloud_conf is not None
        return self._cloud_conf


__all__ = ["CloudMask"]
