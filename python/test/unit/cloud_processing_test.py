from ecostress import CloudProcessing
import geocal
import pytest
import numpy as np
import h5py
import subprocess


class RadianceData:
    """Structured object to store radiance and geolocation data."""

    def __init__(self, radiance, lat=None, lon=None, el=None):
        self.Rad = radiance  # NumPy array for radiance data
        self.Lat = lat  # NumPy array for latitude
        self.Lon = lon  # NumPy array for longitude
        self.El = el  # NumPy array fro elevation


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
            el = geo_hdf["/Geolocation/height"][:] / 1000.0  # convert to km
            return lat, lon, el
    except Exception as e:
        print(f"Error loading geolocation data from {geo_file}: {e}")
        return None, None


def test_process_cloud(isolated_dir, test_data_latest):
    osp_dir = test_data_latest / "l1_osp_dir"
    cloud_lut_fname = osp_dir / "ECOSTRESS_LUT_Cloud_BT11_v3_??.h5"
    rad_lut_fname = osp_dir / "ECOSTRESS_Rad_LUT_v4.txt"
    cloud_fname = "ECOv002_L1_CLOUD_05675_016_20190706T235959.h5"
    geo_fname = (
        test_data_latest / "ECOSTRESS_L1B_GEO_05675_016_20190706T235959_0601_02.h5"
    )
    l1b_rad_fname = (
        test_data_latest / "ECOSTRESS_L1B_RAD_05675_016_20190706T235959_0601_02.h5"
    )
    vrad = load_radiance_data(l1b_rad_fname)
    vrad.Lat, vrad.Lon, vrad.El = load_geolocation_data(geo_fname)
    tstart = geocal.Time.parse_time("2019-07-06T23:59:59Z")
    cprocess = CloudProcessing(rad_lut_fname, cloud_lut_fname)
    cloud, cloudconf = cprocess.process_cloud(vrad, tstart)

    # Write data out, just so we can easily compare with the expected data
    with h5py.File(cloud_fname, "w") as cloudout:
        sds_group = cloudout.create_group("/SDS")
        sds_group.create_dataset("Cloud_confidence", data=cloudconf, dtype=np.uint8)
        sds_group.create_dataset("Cloud_final", data=cloud, dtype=np.uint8)
    
    subprocess.run(
        ["h5diff", "-r", cloud_fname, test_data_latest / f"{cloud_fname}.expected"],
        check=True,
    )


def test_process_cloud2(isolated_dir, test_data_latest):
    osp_dir = test_data_latest / "l1_osp_dir"
    cloud_lut_fname = osp_dir / "ECOSTRESS_LUT_Cloud_BT11_v3_??.h5"
    rad_lut_fname = osp_dir / "ECOSTRESS_Rad_LUT_v4.txt"
    cloud_fname = "ECOv002_L1_CLOUD_27322_005_20230501T155850.h5"
    geo_fname = (
        test_data_latest / "ECOv002_L1B_GEO_27322_005_20230501T155850_0710_01.h5"
    )
    l1b_rad_fname = (
        test_data_latest / "ECOv002_L1B_RAD_27322_005_20230501T155850_0710_02.h5"
    )
    vrad = load_radiance_data(l1b_rad_fname)
    vrad.Lat, vrad.Lon, vrad.El = load_geolocation_data(geo_fname)
    tstart = geocal.Time.parse_time("2023-05-01T15:58:50Z")
    cprocess = CloudProcessing(rad_lut_fname, cloud_lut_fname)
    cloud, cloudconf = cprocess.process_cloud(vrad, tstart)
    
    # Write data out, just so we can easily compare with the expected data
    with h5py.File(cloud_fname, "w") as cloudout:
        sds_group = cloudout.create_group("/SDS")
        sds_group.create_dataset("Cloud_confidence", data=cloudconf, dtype=np.uint8)
        sds_group.create_dataset("Cloud_final", data=cloud, dtype=np.uint8)
    
    subprocess.run(
        ["h5diff", "-r", cloud_fname, test_data_latest / f"{cloud_fname}.expected"],
        check=True,
    )
