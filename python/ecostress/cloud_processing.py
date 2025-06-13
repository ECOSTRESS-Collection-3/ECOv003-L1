import sys
sys.path.insert(0, "/home/vmj/my_numba")
import numpy as np
import h5py
from scipy.interpolate import RegularGridInterpolator
from scipy.interpolate import interp1d
import re
from numba import njit


@njit
def classify_clouds(TB4_flat, BTout1_flat, BTout2_flat, BTout3_flat, El_flat, cloud1, cloudconf):
    for i in range(TB4_flat.size):
        if np.isnan(TB4_flat[i]):
            cloud1[i] = 255
            cloudconf[i] = 255
            continue

        t = TB4_flat[i]
        b1 = BTout1_flat[i]
        b2 = BTout2_flat[i]
        b3 = BTout3_flat[i]
        el = El_flat[i]

        if t > b3:
            cloud1[i] = 0
            cloudconf[i] = 0
        elif b2 < t <= b3:
            cloud1[i] = 0
            cloudconf[i] = 1
        elif b1 < t <= b2:
            cloud1[i] = 0 if el > 2.0 else 1
            cloudconf[i] = 2
        elif t <= b1:
            cloud1[i] = 1
            cloudconf[i] = 3
        else:
            cloud1[i] = 255
            cloudconf[i] = 255


def process_cloud(rad, bt11_lut_file, btdiff_file, rad_lut_data, rad_lut_nlines, cloud_filename):

    #print("Total number of radiance layers in vRAD:", rad.Rad.nchannels)
    print("Shapes of radiance layers:", [r.shape for r in rad.Rad])
    print("Band count:", rad.Rad.shape[0])

    BAND_4 = rad.Rad.shape[0] - 2  # Band index for channel 4
    BAND_5 = BAND_4 + 1            # Band index for channel 5, NOTE: band  is not used in this clould mask aglorithm
    COL_1 = 0
    COL_5 = 4
    COL_6 = 5

    print("CONVERT RADIANCES TO BT")
    nrows, ncols = rad.Rad[BAND_4].shape
    TB4 = np.zeros((nrows, ncols))


    # Ensure the LUT table is sorted in descending order 
    if rad_lut_data[COL_5][-1] < rad_lut_data[COL_5][0]:  # Descending order in aas in C
        sorted_indices = np.argsort(-rad_lut_data[:, COL_5])  # Sort descending
    else:
        sorted_indices = np.argsort(rad_lut_data[:, COL_5])   # Sort ascending

    sorted_x_5 = rad_lut_data[sorted_indices, COL_5]  # Radiance values for Band 4
    sorted_y_5 = rad_lut_data[sorted_indices, COL_1]  # Brightness temperature for Band 4
    
    FILL_VALUE = -9997.0
    # Mask out fill values before interpolation
    valid_mask = rad.Rad[BAND_4] != FILL_VALUE  # Valid pixels (True = keep, False = fill)
    TB4 = np.full((nrows, ncols), np.nan)  # Initialize with NaN

    # Create interpolation function with extrapolation
    interp_func = interp1d(
    sorted_x_5, sorted_y_5, 
        kind="linear", bounds_error=False, fill_value = "extrapolate"
    )
    # Apply interpolation only on valid radiance values
    TB4[valid_mask] = interp_func(rad.Rad[BAND_4][valid_mask])
    
    print("EXTRACT FILE NAME TO GET TIME FOR BT THRESHOLDS")
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
    Ztime0 = 6 * (hh // 6)  # Nearest past 6-hour mark
    Ztime1 = (Ztime0 + 6) % 24  # Next 6-hour mark

    lut_files = {}

    for hour in ["00", "06", "12", "18"]:
        lut_file = bt11_lut_file.replace("??", hour)  # Replace "??" with actual time
        try:
            lut_files[int(hour) // 6] = h5py.File(lut_file, "r")  # Store with index (0,1,2,3)
        except Exception as e:
            raise RuntimeError(f"Unable to open LUT: {lut_file}")


    # Load latitude and longitude from the LUT file corresponding to Ztime1
    lut_index = Ztime1 // 6  # In C, lutid[3] is used; we map it dynamically
    
    try:
        lut_lat = np.transpose(lut_files[lut_index]['/Geolocation/Latitude'][:])
        lut_lon = np.transpose(lut_files[lut_index]['/Geolocation/Longitude'][:])
    except KeyError as e:
        raise RuntimeError(f"Error reading geolocation data from LUT file index {lut_index}: {e}")
 
    sorted_lat = lut_lat                #   not sorting to match C
  
    # Prepare brightness temperature thresholds
    BTout = {i: np.zeros((nrows, ncols)) for i in range(1, 4)}
    slapse = 6.5  # Standard lapse rate

    print("CREATE BT THRESHOLDS")
    for LUTthresh in range(1, 4):  # Iterate over LUT thresholds (1, 2, 3)
        cloudvar1 = f"/Data/LUT_cloudBT{LUTthresh}_{Ztime0:02d}_{mth:02d}"
        cloudvar2 = f"/Data/LUT_cloudBT{LUTthresh}_{Ztime1:02d}_{mth:02d}"

        # Select the correct LUT file index
        lut0 = Ztime0 // 6  # Matches C's lut0 = Ztime0 / 6
        lut1 = Ztime1 // 6  # Matches C's lut1 = Ztime1 / 6

        try:
            BT1 = np.transpose(lut_files[lut0][cloudvar1][:])  # Read and transpose BT1
        except KeyError:
            raise RuntimeError(f"Error: Could not find dataset {cloudvar1} in LUT file index {lut0}.")

        try:
            BT2 = np.transpose(lut_files[lut1][cloudvar2][:])  # Read and transpose BT2
        except KeyError:
            raise RuntimeError(f"Error: Could not find dataset {cloudvar2} in LUT file index {lut1}.")

       
        sorted_BT1 = BT1 # not sorting to match C
        sorted_BT2 = BT2 # not sorting to match C

        #in case of debug 
        #np.savetxt("BT1.csv", BT1, delimiter=",")
        #np.savetxt("BT2.csv", BT2, delimiter=",")
        #print("Saved BT1.csv and BT2.csv")

        # Create RegularGridInterpolator functions with sorted latitude
        interp_BT1 = RegularGridInterpolator(
            (sorted_lat[:, 0], lut_lon[0, :]),  # Sorted latitude, unchanged longitude
            sorted_BT1,
            method="linear",
            bounds_error=False,
            fill_value=np.nan
        )

        interp_BT2 = RegularGridInterpolator(
            (sorted_lat[:, 0], lut_lon[0, :]),
            sorted_BT2,
            method="linear",
            bounds_error=False,
            fill_value=np.nan
        )

        # Vectorized interpolation
        points = np.column_stack((rad.Lat.ravel(), rad.Lon.ravel()))
        BTgrid1_interp = interp_BT1(points).reshape(nrows, ncols)
        BTgrid2_interp = interp_BT2(points).reshape(nrows, ncols)

        # Temporal interpolation
        m = (hrfrac - Ztime0) / 6.0
        BT = BTgrid1_interp + m * (BTgrid2_interp - BTgrid1_interp)

        # Initialize BTout correctly (C explicitly allocates BT)
        BTout[LUTthresh] = np.full((nrows, ncols), 255, dtype=np.float64)  # Default to 255

        # Apply cloud test correction (Ensure NaN handling is robust)        
        valid_mask = ~np.isnan(TB4) & ~np.isnan(rad.El)  # Avoid NaN issues
        BTout[LUTthresh][valid_mask] = BT[valid_mask] - rad.El[valid_mask] * slapse
        
    print("CLOUD MASK GENERATION")
    cloud1 = np.full((nrows, ncols), 255, dtype=np.uint8)
    cloudconf = np.full((nrows, ncols), 255, dtype=np.uint8)

    # Flatten arrays for easy iteration (sort of similar to indexing in C)
    
    TB4_flat = TB4.ravel()
    BTout1_flat = BTout[1].ravel()
    BTout2_flat = BTout[2].ravel()
    BTout3_flat = BTout[3].ravel()
    El_flat = rad.El.ravel()
    cloud1_flat = cloud1.ravel()
    cloudconf_flat = cloudconf.ravel()

    # calssify clouds translated from below to a numba function 
    classify_clouds(TB4_flat, BTout1_flat, BTout2_flat, BTout3_flat, El_flat, cloud1_flat, cloudconf_flat)
    # Reshape if needed
    cloud1 = cloud1_flat.reshape((nrows, ncols))
    cloudconf = cloudconf_flat.reshape((nrows, ncols))

    """
    # **Cloud Classification**
    for i in range(nrows * ncols):
        if np.isnan(TB4_flat[i]):
            cloud1.flat[i] = 255
            cloudconf.flat[i] = 255
            continue  # Skip the rest of the checks

        # Logic copied from c program "Bob Freepartner" 
        confidentcloud = TB4_flat[i] <= BTout1_flat[i]
        probablycloud  = (BTout1_flat[i] < TB4_flat[i] <= BTout2_flat[i])
        probablyclear  = (BTout2_flat[i] < TB4_flat[i] <= BTout3_flat[i])
        confidentclear = TB4_flat[i] > BTout3_flat[i]

        if confidentclear:
            cloud1.flat[i] = 0
            cloudconf.flat[i] = 0
        elif probablyclear:
            cloud1.flat[i] = 0
            cloudconf.flat[i] = 1
        elif probablycloud:
            # At altitude > 2 km consider probablycloud as clear
            cloud1.flat[i] = 0 if El_flat[i] > 2.0 else 1
            cloudconf.flat[i] = 2
        elif confidentcloud:
            cloud1.flat[i] = 1
            cloudconf.flat[i] = 3
        else:
            cloud1.flat[i] = 255
            cloudconf.flat[i] = 255
    """

    print("WRITE CLOUD MASK FILE")
    with h5py.File(cloud_filename, "w") as cloudout:
        sds_group = cloudout.create_group("/SDS")
        sds_group.create_dataset("Cloud_confidence", data=cloudconf, dtype=np.uint8)
        sds_group.create_dataset("Cloud_final", data=cloud1, dtype=np.uint8)

    # Cleanup
    for file in lut_files.values():  # Iterate 
        if isinstance(file, h5py.File):  # ck
            file.close()
