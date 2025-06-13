from cloud_processing import process_cloud
from fileio import load_radiance_data, load_lookup_table, load_geolocation_data

# Configuration parameters
CLOUD_LUT_FILE = "/project/sandbox/vmj/TestCloudMask/OSP/ECOSTRESS_LUT_Cloud_BT11_v3_??.h5"
CLOUD_BTDIFF_FILE = "/project/sandbox/vmj/TestCloudMask/OSP/cloud_BTdiff_4minus5_ecostress.h5"
RAD_LUT_FILE = "/project/sandbox/vmj/TestCloudMask/OSP/ECOSTRESS_Rad_LUT_v4.txt"
CLOUD_FILENAME = "/home/vmj/sandbox/TestCloudMask/test_27322_005/output/ECOv002_L1_CLOUD_27322_005_20230501T155850_test1.h5"
GEO_FILENAME = "/ops/store14/PRODUCTS/L1B_GEO/2023/05/01/ECOv002_L1B_GEO_27322_005_20230501T155850_0710_01.h5"
L1B_RAD_FILE = "/ops/store14/PRODUCTS/L1B_RAD/2023/05/01/ECOv002_L1B_RAD_27322_005_20230501T155850_0710_02.h5"

# Load radiance data (structured)
vRAD = load_radiance_data(L1B_RAD_FILE)

# Load lookup table
lut, nlut_lines = load_lookup_table(RAD_LUT_FILE)

# Load geolocation data
lat, lon, el = load_geolocation_data(GEO_FILENAME)

# Attach lat/lon data to the radiance structure
if vRAD is not None:
    vRAD.Lat = lat
    vRAD.Lon = lon
    vRAD.El = el

# Ensure geolocation data was loaded properly
if lat is None or lon is None:
    raise RuntimeError("Geolocation data could not be loaded. Check the GEO file.")

# Process cloud with geolocation data
detected_clouds = process_cloud(vRAD, CLOUD_LUT_FILE, CLOUD_BTDIFF_FILE, lut, nlut_lines, CLOUD_FILENAME)

# Output results
print("Cloud processing completed. Output saved to:", CLOUD_FILENAME)
