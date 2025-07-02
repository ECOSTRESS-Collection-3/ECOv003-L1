from __future__ import annotations
from ecostress_swig import (  # type: ignore
    FILL_VALUE_NOT_SEEN,
)
import numpy as np
import h5py  # type: ignore
import warnings
import os

# Have a warning message that we can't do anything about - suppress it
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    import scipy.interpolate  # type: ignore
import re
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    import geocal  # type: ignore


class CloudProcessing:
    def __init__(
        self, rad_lut_fname: str | os.PathLike, b11_lut_file_pattern: str | os.PathLike
    ) -> None:
        """Initialize cloud processing. The rad_lut_fname is found in
        our l1_osp_dir and this is a lookup table mapping band 4 radiance
        to brightness temperature.

        The bt11_lut_file_pattern should have "??" in the name as a placeholder,
        we use this to determine the names at 6 hour intervals"""

        # Read the LUT data.
        self.rad_lut_data = np.loadtxt(rad_lut_fname, dtype=np.float64)

        # Create interpolation function with extrapolation. Index 4 is the
        # radiance value, index 0 is the brightness temperature
        #
        # Note that the C code needs
        # to have this sorted, but scipy interp1d doesn't need this - it
        # sorts the data itself.
        self.rad_to_bt_interpolate = scipy.interpolate.interp1d(
            self.rad_lut_data[:, 4],
            self.rad_lut_data[:, 0],
            kind="linear",
            bounds_error=False,
            fill_value="extrapolate",
        )

        self._b11_lut_fname: dict[int, h5py.File] = {}
        for hour in ["00", "06", "12", "18"]:
            fname = str(b11_lut_file_pattern).replace("??", hour)
            self._b11_lut_fname[int(hour)] = fname

    def bt11_interpolator(
        self, hour: int, month: int
    ) -> list[scipy.interpolate.RegularGridInterpolator]:
        """Take the given hour (which should be a multiple of 6) and
        month and return three interpolators mapping lat/lon to the
        brightness temperature threshold 1, 2 and 3
        """
        res = []
        with h5py.File(self._b11_lut_fname[hour]) as f:
            lut_lat = np.transpose(f["/Geolocation/Latitude"][:])
            lut_lon = np.transpose(f["/Geolocation/Longitude"][:])
            for lut_thresh in range(1, 4):  # Iterate over LUT thresholds (1, 2, 3)
                cloudvar1 = f"/Data/LUT_cloudBT{lut_thresh}_{hour:02d}_{month:02d}"
                bt = np.transpose(f[cloudvar1][:])
                res.append(
                    scipy.interpolate.RegularGridInterpolator(
                        (lut_lat[:, 0], lut_lon[0, :]),
                        bt,
                        method="linear",
                        bounds_error=False,
                        fill_value=np.nan,
                    )
                )
        return res

    def convert_radiance_to_bt(self, rad_band_4: np.ndarray) -> np.ndarray:
        """Convert band 4 radiance to brightness temperature"""
        logger.debug("Convert radiances to BT")
        tb4 = np.full(rad_band_4.shape, np.nan)
        valid_mask = rad_band_4 != FILL_VALUE_NOT_SEEN
        tb4[valid_mask] = self.rad_to_bt_interpolate(rad_band_4[valid_mask])
        return tb4

    def classify_clouds(self, tb4, bt_out, height_meter):
        # Mark cloud, just so we can more easily handle the if/else logic here. We can
        # make sure to only update values at each step that weren't done before.
        cloud1 = np.full(tb4.shape, 128, dtype=np.uint8)
        cloudconf = np.full(cloud1.shape, 128, dtype=np.uint8)

        # Skip any nans,
        cloud1[np.isnan(tb4)] = 255
        cloudconf[np.isnan(tb4)] = 255

        # Confident clear
        cloud1[(cloud1 == 128) & (tb4 > bt_out[3])] = 0
        cloudconf[(cloudconf == 128) & (tb4 > bt_out[3])] = 0

        # Probably clear
        cloud1[(cloud1 == 128) & (tb4 <= bt_out[3]) & (tb4 > bt_out[2])] = 0
        cloudconf[(cloudconf == 128) & (tb4 <= bt_out[3]) & (tb4 > bt_out[2])] = 1

        # Probably cloudy
        cloud1[(cloud1 == 128) & (tb4 <= bt_out[2]) & (tb4 > bt_out[1])] = 0
        cloudconf[(cloudconf == 128) & (tb4 <= bt_out[2]) & (tb4 > bt_out[1])] = 2

        # Confident cloudy
        cloud1[(cloud1 == 128) & (tb4 <= bt_out[1])] = 1
        cloudconf[(cloudconf == 128) & (tb4 <= bt_out[1])] = 3

        # Fill in anything that didn't get a  value
        cloud1[cloud1 == 128] = 255
        cloudconf[cloudconf == 128] = 255

        return cloud1, cloudconf

    def parse_time(self, tstart: geocal.Time) -> tuple[int, int, int]:
        """Parse the start time for the radiance data, returning month, hour, and minute."""
        # geocal time string in a standard CCSDS string, so we know the format.
        m = re.match(
            r"(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d\.\d+)Z", str(tstart)
        )
        if m is None:
            raise RuntimeError("Trouble parsing time string")
        return (int(m[2]), int(m[4]), int(m[5]))

    def process_cloud(
        self,
        rad_band_4: np.ndarray,
        latitude: np.ndarray,
        longitude: np.ndarray,
        height_meter: np.ndarray,
        tstart: geocal.Time,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Process the given band 4 radiance data to determine the cloud mask.

        The latitude and longitude is the initial guess since we need the
        cloud mask before we have corrected the pointing. According to Glynn this
        should be fine, the cloud mask doesn't change that fast with latitude and
        longitude. In any case, we call this a "prelim_cloud_mask", there is
        another one calculated in L2 after we have corrected the pointing of
        the radiance data.

        This returns two arrays, a cloud mask and a cloud confidence mask.

        The cloud mask is 0 for clear, 1 for cloudy, or 255 for pixels that
        can't be computed (e.g., the radiance data is fill).

        The cloud confidence is 0 - confident clear 1 - probably clear, 2 - probably cloud
        and 3 - probably cloudy. It is 255 for pixels that can't be computed."""

        tb4 = self.convert_radiance_to_bt(rad_band_4)

        month, hour, minute = self.parse_time(tstart)

        # Compute 6-hour time intervals, and use to determine the b11 LUT file we use
        hrfrac = hour + minute / 60.0
        ztime0 = 6 * (hour // 6)  # Nearest past 6-hour mark
        ztime1 = (ztime0 + 6) % 24  # Next 6-hour mark

        logger.debug("Create bt thresholds")
        bt_out = {i: np.zeros(tb4.shape) for i in range(1, 4)}
        slapse_km = 6.5  # Standard lapse rate
        slapse_meter = slapse_km / 1000.0
        interp_bt1 = self.bt11_interpolator(ztime0, month)
        interp_bt2 = self.bt11_interpolator(ztime1, month)
        for lut_thresh in range(1, 4):  # Iterate over LUT thresholds (1, 2, 3)
            # Vectorized interpolation
            points = np.column_stack((latitude.ravel(), longitude.ravel()))
            btgrid1_interp = interp_bt1[lut_thresh - 1](points).reshape(tb4.shape)
            btgrid2_interp = interp_bt2[lut_thresh - 1](points).reshape(tb4.shape)

            # Temporal interpolation
            m = (hrfrac - ztime0) / 6.0
            bt = btgrid1_interp + m * (btgrid2_interp - btgrid1_interp)

            # Initialize bt_out correctly (C explicitly allocates bt)
            bt_out[lut_thresh] = np.full(
                tb4.shape, 255, dtype=np.float64
            )  # Default to 255

            # Apply cloud test correction (Ensure NaN handling is robust)
            valid_mask = ~np.isnan(tb4) & ~np.isnan(height_meter)  # Avoid NaN issues
            bt_out[lut_thresh][valid_mask] = (
                bt[valid_mask] - height_meter[valid_mask] * slapse_meter
            )

        logger.debug("Cloud mask generation")

        # classify clouds
        cloud1, cloudconf = self.classify_clouds(tb4, bt_out, height_meter)

        return (cloud1, cloudconf)


__all__ = [
    "CloudProcessing",
]
