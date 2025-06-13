import numpy as np

def load_lookup_table(lut_file, num_columns=6):
    """
    Load the lookup table from a text file.

    Parameters:
        lut_file (str): Path to the lookup table file.
        num_columns (int): Number of columns in the LUT file.

    Returns:
        tuple: (lut, nlut_lines)
            - lut (np.ndarray): A NumPy 2D array containing the LUT data.
            - nlut_lines (int): The number of lines in the LUT file.
    """
    try:
        # Read the LUT file into a NumPy array
        data = np.loadtxt(lut_file, dtype=np.float64)

        # Check if the LUT file has the expected structure
        if data.shape[1] != num_columns:
            raise ValueError(f"Expected {num_columns} columns in LUT file, found {data.shape[1]}.")

        nlut_lines = data.shape[0]  # Number of lines (rows) in the LUT

        # Ensure the file has at least two lines for interpolation
        if nlut_lines < 2:
            raise ValueError(f"File {lut_file} is invalid. Must have at least two lines of values.")

        # Reverse the order of rows to match C behavior
        data = np.flipud(data)

        return data, nlut_lines

    except Exception as e:
        print(f"Error loading lookup table from {lut_file}: {e}")
        return None, None



import h5py

class RadianceData:
    """Structured object to store radiance and geolocation data."""
    def __init__(self, radiance, lat=None, lon=None, el=None):
        self.Rad = radiance  # NumPy array for radiance data
        self.Lat = lat       # NumPy array for latitude
        self.Lon = lon       # NumPy array for longitude
        self.El = el         # NumPy array fro elevation

def load_radiance_data(hdf5_file):
    """
    Load radiance data from an HDF5 file.

    Parameters:
        hdf5_file (str): Path to the HDF5 file containing radiance data.

    Returns:
        list: A list of NumPy arrays containing radiance data for different bands.
    """
    try:
        with h5py.File(hdf5_file, "r") as hdf:
            rad1 = hdf["/Radiance/radiance_1"][:]
            rad2 = hdf["/Radiance/radiance_2"][:]
            rad3 = hdf["/Radiance/radiance_3"][:]
            rad4 = hdf["/Radiance/radiance_4"][:]  # BAND_4
            rad5 = hdf["/Radiance/radiance_5"][:]  # BAND_5

        # Stack the radiance bands into a single NumPy array (shape: [5, height, width])
        radiance_data = np.stack([rad1, rad2, rad3, rad4, rad5], axis=0)
        
        return RadianceData(radiance_data)

    except Exception as e:
        print(f"Error loading radiance data from {hdf5_file}: {e}")
        return None

def load_geolocation_data(geo_file):
    """
    Load latitude and longitude data from the GEO file.

    Parameters:
        geo_file (str): Path to the GEO HDF5 file.

    Returns:
        tuple: (Latitude array, Longitude array, Elevation array)
    """
    try:
        with h5py.File(geo_file, "r") as geo_hdf:
            lat = geo_hdf["/Geolocation/latitude"][:]
            lon = geo_hdf["/Geolocation/longitude"][:]
            el = geo_hdf["/Geolocation/height"][:] / 1000.0 # convert to km
            return lat, lon, el
    except Exception as e:
        print(f"Error loading geolocation data from {geo_file}: {e}")
        return None, None

import h5py

def load_lut_files(bt11_lut_file):
    """
    Load the brightness temperature LUT files for the 6-hour intervals.

    Parameters:
        bt11_lut_file (str): Path pattern to the LUT file containing "??" as a placeholder.

    Returns:
        list: A list of opened HDF5 LUT file objects.
    """
    hour_strings = ["00", "06", "12", "18"]  # 6-hour intervals
    lut_files = []

    # Ensure that the file pattern contains "??"
    if "??" not in bt11_lut_file:
        raise RuntimeError(f"cloudLUT file path is missing '??': {bt11_lut_file}")

    for hour in hour_strings:
        # Replace "??" with the actual hour string
        lut_file = bt11_lut_file.replace("??", hour)
        try:
            hdf5_file = h5py.File(lut_file, "r")  # Open the LUT file in read mode
            lut_files.append(hdf5_file)
            print(f"Loaded LUT file: {lut_file}")  # Debugging output
        except Exception as e:
            raise RuntimeError(f"Unable to open LUT: {lut_file} - {e}")

    return lut_files  # List of opened HDF5 LUT files

