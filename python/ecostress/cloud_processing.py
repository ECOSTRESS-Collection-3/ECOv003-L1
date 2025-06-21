import sys
from ecostress_swig import (  # type: ignore
    FILL_VALUE_NOT_SEEN,
)
import numpy as np
import h5py
import warnings
import os
# Have a warning message that we can't do anything about - suppress it
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    import scipy.interpolate
    from scipy.interpolate import RegularGridInterpolator
    from scipy.interpolate import interp1d
import re
from loguru import logger

class CloudProcessing:
    def __init__(self, rad_lut_fname : str | os.PathLike) -> None:
        # Read the LUT data.
        self.rad_lut_data = np.loadtxt(rad_lut_fname, dtype=np.float64)
        
        # Create interpolation function with extrapolation. Index 4 is the
        # radiance value, index 0 is the brightness temperature
        #
        # Note that the C code needs
        # to have this sorted, but scipy interp1d doesn't need this - it
        # sorts the data itself.
        self.rad_to_bt_interpolate = scipy.interpolate.interp1d(
            self.rad_lut_data[:,4], self.rad_lut_data[:,0], 
            kind="linear", bounds_error=False, fill_value = "extrapolate"
        )
    
    def classify_clouds(self, tb4, bt_out, el):
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
        # At altitude > 2 km consider probablycloud as clear
        cloud1[(cloud1 == 128) & (tb4 <= bt_out[2]) & (tb4 > bt_out[1]) & (el > 2.0)] = 0
        # Otherwise, mark as cloudy
        cloud1[(cloud1 == 128) & (tb4 <= bt_out[2]) & (tb4 > bt_out[1]) & (el <= 2.0)] = 1
        cloudconf[(cloudconf == 128) & (tb4 <= bt_out[2]) & (tb4 > bt_out[1])] = 2
    
        # Confident cloudy
        cloud1[(cloud1 == 128) & (tb4 <= bt_out[1])] = 1
        cloudconf[(cloudconf == 128) & (tb4 <= bt_out[1])] = 3
    
        # Fill in anything that didn't get a  value
        cloud1[cloud1 == 128] = 255
        cloudconf[cloudconf == 128] = 255
    
        return cloud1, cloudconf
    
    def process_cloud(self, rad, bt11_lut_file, btdiff_file, cloud_filename):
        logger.debug(f"Shapes of radiance layers: {[r.shape for r in rad.Rad]}")
        logger.debug(f"Band count: {rad.Rad.shape[0]}")
    
        band_4 = rad.Rad.shape[0] - 2  # Band index for channel 4
        band_5 = band_4 + 1            # Band index for channel 5, NOTE: band  is not used in this clould mask aglorithm
        col_1 = 0
        col_5 = 4
        col_6 = 5
    
        logger.debug("Convert radiances to BT")
        nrows, ncols = rad.Rad[band_4].shape
        tb4 = np.zeros((nrows, ncols))
    
        # Mask out fill values before interpolation
        # Valid pixels (True = keep, False = fill)
        valid_mask = rad.Rad[band_4] != FILL_VALUE_NOT_SEEN  
        tb4 = np.full((nrows, ncols), np.nan)  # Initialize with NaN
    
        # Apply interpolation only on valid radiance values
        tb4[valid_mask] = self.rad_to_bt_interpolate(rad.Rad[band_4][valid_mask])
        
        logger.debug("Extract file name to get time for bt thresholds")
        filename_parts = cloud_filename.split("/")[-1]
    
        # Find the position of "L1_CLOUD" in the filename
        match = re.search(r"L1_CLOUD", filename_parts)
        if not match:
            raise RuntimeError(f"L1_CLOUD not found in filename: {cloud_filename}")
    
        # Extract `mth` and `hh`, `mm` relative to "L1_CLOUD"
        start_idx = match.start()
        mth = int(filename_parts[start_idx + 23:start_idx + 25])  # Month
        hh = int(filename_parts[start_idx + 28:start_idx + 30])  # Hour
        mm = int(filename_parts[start_idx + 30:start_idx + 32])  # Minute
    
        # Ensure values are reasonable
        if not (1 <= mth <= 12):
            raise RuntimeError(f"Invalid month extracted: {mth} from {cloud_filename}")
        if not (0 <= hh < 24):
            raise RuntimeError(f"Invalid hour extracted: {hh} from {cloud_filename}")
        if not (0 <= mm < 60):
            raise RuntimeError(f"Invalid minute extracted: {mm} from {cloud_filename}")
    
        # Compute 6-hour time intervals
        hrfrac = hh + mm / 60.0
        ztime0 = 6 * (hh // 6)  # Nearest past 6-hour mark
        ztime1 = (ztime0 + 6) % 24  # Next 6-hour mark
    
        lut_files = {}
    
        for hour in ["00", "06", "12", "18"]:
            lut_file = str(bt11_lut_file).replace("??", hour)  # Replace "??" with actual time
            try:
                lut_files[int(hour) // 6] = h5py.File(lut_file, "r")  # Store with index (0,1,2,3)
            except Exception as e:
                raise RuntimeError(f"Unable to open LUT: {lut_file}")
    
    
        # Load latitude and longitude from the LUT file corresponding to ztime1
        lut_index = ztime1 // 6  # In C, lutid[3] is used; we map it dynamically
        
        try:
            lut_lat = np.transpose(lut_files[lut_index]['/Geolocation/Latitude'][:])
            lut_lon = np.transpose(lut_files[lut_index]['/Geolocation/Longitude'][:])
        except KeyError as e:
            raise RuntimeError(f"Error reading geolocation data from LUT file index {lut_index}: {e}")
     
        sorted_lat = lut_lat                #   not sorting to match C
      
        # Prepare brightness temperature thresholds
        bt_out = {i: np.zeros((nrows, ncols)) for i in range(1, 4)}
        slapse = 6.5  # Standard lapse rate
    
        logger.debug("Create bt thresholds")
        for lut_thresh in range(1, 4):  # Iterate over LUT thresholds (1, 2, 3)
            cloudvar1 = f"/Data/LUT_cloudBT{lut_thresh}_{ztime0:02d}_{mth:02d}"
            cloudvar2 = f"/Data/LUT_cloudBT{lut_thresh}_{ztime1:02d}_{mth:02d}"
    
            # Select the correct LUT file index
            lut0 = ztime0 // 6  # Matches C's lut0 = ztime0 / 6
            lut1 = ztime1 // 6  # Matches C's lut1 = ztime1 / 6
    
            try:
                bt1 = np.transpose(lut_files[lut0][cloudvar1][:])  # Read and transpose bt1
            except KeyError:
                raise RuntimeError(f"Error: Could not find dataset {cloudvar1} in LUT file index {lut0}.")
    
            try:
                bt2 = np.transpose(lut_files[lut1][cloudvar2][:])  # Read and transpose bt2
            except KeyError:
                raise RuntimeError(f"Error: Could not find dataset {cloudvar2} in LUT file index {lut1}.")
    
           
            sorted_bt1 = bt1 # not sorting to match C
            sorted_bt2 = bt2 # not sorting to match C
    
            #in case of debug 
            #np.savetxt("bt1.csv", bt1, delimiter=",")
            #np.savetxt("bt2.csv", bt2, delimiter=",")
            #print("Saved bt1.csv and bt2.csv")
    
            # Create RegularGridInterpolator functions with sorted latitude
            interp_bt1 = RegularGridInterpolator(
                (sorted_lat[:, 0], lut_lon[0, :]),  # Sorted latitude, unchanged longitude
                sorted_bt1,
                method="linear",
                bounds_error=False,
                fill_value=np.nan
            )
    
            interp_bt2 = RegularGridInterpolator(
                (sorted_lat[:, 0], lut_lon[0, :]),
                sorted_bt2,
                method="linear",
                bounds_error=False,
                fill_value=np.nan
            )
    
            # Vectorized interpolation
            points = np.column_stack((rad.Lat.ravel(), rad.Lon.ravel()))
            btgrid1_interp = interp_bt1(points).reshape(nrows, ncols)
            btgrid2_interp = interp_bt2(points).reshape(nrows, ncols)
    
            # Temporal interpolation
            m = (hrfrac - ztime0) / 6.0
            bt = btgrid1_interp + m * (btgrid2_interp - btgrid1_interp)
    
            # Initialize bt_out correctly (C explicitly allocates bt)
            bt_out[lut_thresh] = np.full((nrows, ncols), 255, dtype=np.float64)  # Default to 255
    
            # Apply cloud test correction (Ensure NaN handling is robust)        
            valid_mask = ~np.isnan(tb4) & ~np.isnan(rad.El)  # Avoid NaN issues
            bt_out[lut_thresh][valid_mask] = bt[valid_mask] - rad.El[valid_mask] * slapse
            
        logger.debug("Cloud mask generation")
    
        # classify clouds
        cloud1, cloudconf = self.classify_clouds(tb4, bt_out, rad.El)
    
        """
        # **Cloud Classification**
        for i in range(nrows * ncols):
            if np.isnan(tb4_flat[i]):
                cloud1.flat[i] = 255
                cloudconf.flat[i] = 255
                continue  # Skip the rest of the checks
    
            # Logic copied from c program "Bob Freepartner" 
            confidentcloud = tb4_flat[i] <= bt_out1_flat[i]
            probablycloud  = (bt_out1_flat[i] < tb4_flat[i] <= bt_out2_flat[i])
            probablyclear  = (bt_out2_flat[i] < tb4_flat[i] <= bt_out3_flat[i])
            confidentclear = tb4_flat[i] > bt_out3_flat[i]
    
            if confidentclear:
                cloud1.flat[i] = 0
                cloudconf.flat[i] = 0
            elif probablyclear:
                cloud1.flat[i] = 0
                cloudconf.flat[i] = 1
            elif probablycloud:
                # At altitude > 2 km consider probablycloud as clear
                cloud1.flat[i] = 0 if el_flat[i] > 2.0 else 1
                cloudconf.flat[i] = 2
            elif confidentcloud:
                cloud1.flat[i] = 1
                cloudconf.flat[i] = 3
            else:
                cloud1.flat[i] = 255
                cloudconf.flat[i] = 255
        """
    
        logger.debug("Write Cloud mask file")
        with h5py.File(cloud_filename, "w") as cloudout:
            sds_group = cloudout.create_group("/SDS")
            sds_group.create_dataset("Cloud_confidence", data=cloudconf, dtype=np.uint8)
            sds_group.create_dataset("Cloud_final", data=cloud1, dtype=np.uint8)
    
        # Cleanup
        for file in lut_files.values():  # Iterate 
            if isinstance(file, h5py.File):  # ck
                file.close()

__all__ = ["CloudProcessing",]            
