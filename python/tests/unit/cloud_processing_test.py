from ecostress import CloudProcessing
import geocal
import numpy as np
import h5py
import subprocess


def test_process_cloud(isolated_dir, test_data_latest):
    osp_dir = test_data_latest / "l1_osp_dir"
    cloud_lut_fname = osp_dir / "ECOSTRESS_LUT_Cloud_BT11_v3_??.h5"
    rad_lut_fname = osp_dir / "ECOSTRESS_Rad_LUT_v4.txt"
    cloud_fname = "ECOv003_L1_CLOUD_05675_016_20190706T235959.h5"
    geo_fname = (
        test_data_latest / "ECOSTRESS_L1B_GEO_05675_016_20190706T235959_0601_02.h5"
    )
    l1b_rad_fname = (
        test_data_latest / "ECOSTRESS_L1B_RAD_05675_016_20190706T235959_0601_02.h5"
    )
    rad = h5py.File(l1b_rad_fname, "r")["/Radiance/radiance_4"][:]
    f = h5py.File(geo_fname, "r")
    lat = f["/Geolocation/latitude"][:]
    lon = f["/Geolocation/longitude"][:]
    height_meter = f["/Geolocation/height"][:]
    tstart = geocal.Time.parse_time("2019-07-07T00:00:26.221089Z")

    cprocess = CloudProcessing(rad_lut_fname, cloud_lut_fname)
    cloud, cloudconf = cprocess.process_cloud(rad, lat, lon, height_meter, tstart)

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
    cloud_fname = "ECOv003_L1_CLOUD_27322_005_20230501T155850.h5"
    geo_fname = (
        test_data_latest / "ECOv002_L1B_GEO_27322_005_20230501T155850_0710_01.h5"
    )
    l1b_rad_fname = (
        test_data_latest / "ECOv002_L1B_RAD_27322_005_20230501T155850_0710_02.h5"
    )
    rad = h5py.File(l1b_rad_fname, "r")["/Radiance/radiance_4"][:]
    f = h5py.File(geo_fname, "r")
    lat = f["/Geolocation/latitude"][:]
    lon = f["/Geolocation/longitude"][:]
    height_meter = f["/Geolocation/height"][:]
    tstart = geocal.Time.parse_time("2023-05-01T15:58:50Z")

    cprocess = CloudProcessing(rad_lut_fname, cloud_lut_fname)
    cloud, cloudconf = cprocess.process_cloud(rad, lat, lon, height_meter, tstart)

    # Write data out, just so we can easily compare with the expected data
    with h5py.File(cloud_fname, "w") as cloudout:
        sds_group = cloudout.create_group("/SDS")
        sds_group.create_dataset("Cloud_confidence", data=cloudconf, dtype=np.uint8)
        sds_group.create_dataset("Cloud_final", data=cloud, dtype=np.uint8)

    subprocess.run(
        ["h5diff", "-r", cloud_fname, test_data_latest / f"{cloud_fname}.expected"],
        check=True,
    )
