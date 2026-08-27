from __future__ import annotations
import geocal  # type: ignore
from ecostress_swig import FILL_VALUE_NOT_SEEN, Resampler, fill_value_threshold  # type: ignore
from .misc import determine_rotated_map_igc
import os
import h5py  # type: ignore
import numpy as np
import scipy  # type: ignore
import subprocess
from loguru import logger
import typing
from pathlib import Path

if typing.TYPE_CHECKING:
    from .l1b_geo_generate import L1bGeoGenerate


class L1bGeoGenerateTiff(object):
    """This generates a geotiff file of the matching band, and a reference data
    for it. This is useful for diagnostic, to look at geolocation
    it saves having to generate this yourself.
    """

    def __init__(
        self,
        l1b_geo_process: L1bGeoProcess,
        l1b_geo_generate: L1bGeoGenerate,
        l1b_rad: Path,
        output_base_name: Path,
        number_subpixel: int = 3,
    ) -> None:
        self.l1b_geo_process = l1b_geo_process
        self.l1b_geo_generate = l1b_geo_generate
        self.l1b_rad = l1b_rad
        self.output_base_name = output_base_name
        self.number_subpixel = number_subpixel

    def run(self) -> None:
        ortho_base = self.l1b_geo_process.ortho_base_day
        ortho_scale = round(60.0 / ortho_base.map_info.resolution_meter)
        mi = ortho_base.map_info.scale(ortho_scale, ortho_scale)
        if (
            np.count_nonzero(self.l1b_geo_generate.lat < fill_value_threshold) == 0
            and np.count_nonzero(self.l1b_geo_generate.lon < fill_value_threshold) == 0
        ):
            lat = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lat, self.number_subpixel, order=2
            )
            lon = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lon, self.number_subpixel, order=2
            )
        else:
            # But if we do, have special handling
            #
            # Order here of "1" is bilinear. We can't use higher order since we
            # may have missing data and this gets spread out with higher order
            # interpolation. As an easy way of handling this, we set
            # missing data as extremely negative value
            latv = self.l1b_geo_generate.lat.copy()
            lonv = self.l1b_geo_generate.lon.copy()
            latv[latv < fill_value_threshold] = -1e20
            lonv[lonv < fill_value_threshold] = -1e20
            lat = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lat, self.number_subpixel, order=1
            )
            lon = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lon, self.number_subpixel, order=1
            )
        res = Resampler(lon, lat, mi, self.number_subpixel)
        rad_data = geocal.GdalRasterImage(
            f'HDF5:"{self.l1b_rad}"://Radiance/radiance_{self.l1b_geo_process.l1b_geo_config.ecostress_day_band}'
        )
        fname = f"{self.output_base_name.stem}_proj.img"
        fname2 = f"{self.output_base_name.stem}_proj.tif"
        fname3 = f"{self.output_base_name.stem}_ref.tif"
        fname4 = f"{self.output_base_name.stem}_ref_enh.tif"
        res.resample_field(str(fname), rad_data, 100.0, "HALF", True)
        subprocess.run(["gdalenhance", "-equalize", fname, fname2])
        ortho_base.create_subset_file(str(fname3), "GTIFF", [], res.map_info, "-ot Int16")
        subprocess.run(["gdalenhance", "-equalize", fname3, fname4])

__all__ = ["L1bGeoGenerateTiff"]
