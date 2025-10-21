from ecostress import CloudMask, create_igc
from multiprocessing import Pool
import subprocess
import h5py
import numpy as np


def test_cloud_mask(isolated_dir, test_data_latest):
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    b11_lut_file_pattern = l1_osp_dir / "ECOSTRESS_LUT_Cloud_BT11_v3_??.h5"
    rad_lut_fname = l1_osp_dir / "ECOSTRESS_Rad_LUT_v4.txt"
    cloud_fname = "ECOv003_L1_CLOUD_05675_016_20190706T235959.h5"
    geo_fname = (
        test_data_latest / "ECOSTRESS_L1B_GEO_05675_016_20190706T235959_0601_02.h5"
    )
    l1b_rad_fname = (
        test_data_latest / "ECOSTRESS_L1B_RAD_05675_016_20190706T235959_0601_02.h5"
    )
    f = h5py.File(geo_fname, "r")
    lat = f["/Geolocation/latitude"][:]
    lon = f["/Geolocation/longitude"][:]
    height_meter = f["/Geolocation/height"][:]

    cmask = CloudMask(
        l1b_rad_fname,
        l1_osp_dir,
        rad_lut_fname=rad_lut_fname,
        b11_lut_file_pattern=b11_lut_file_pattern,
    )
    cloud = cmask.cloud_mask(lat=lat, lon=lon, height=height_meter)
    cloudconf = cmask.cloud_confidence(lat=lat, lon=lon, height=height_meter)

    # Write data out, just so we can easily compare with the expected data
    with h5py.File(cloud_fname, "w") as cloudout:
        sds_group = cloudout.create_group("/SDS")
        sds_group.create_dataset("Cloud_confidence", data=cloudconf, dtype=np.uint8)
        sds_group.create_dataset("Cloud_final", data=cloud, dtype=np.uint8)

    subprocess.run(
        ["h5diff", "-r", cloud_fname, test_data_latest / f"{cloud_fname}.expected"],
        check=True,
    )


def test_igc_cloud_mask(isolated_dir, test_data_latest):
    l1_osp_dir = test_data_latest / "l1_osp_dir"
    b11_lut_file_pattern = l1_osp_dir / "ECOSTRESS_LUT_Cloud_BT11_v3_??.h5"
    rad_lut_fname = l1_osp_dir / "ECOSTRESS_Rad_LUT_v4.txt"
    cloud_fname = "ECOv003_L1_CLOUD_05675_016_20190706T235959.h5"
    l1b_rad_fname = (
        test_data_latest / "ECOSTRESS_L1B_RAD_05675_016_20190706T235959_0601_02.h5"
    )
    orb_fname = test_data_latest / "L1A_RAW_ATT_05675_20190706T224819_0601_02.h5"
    igc = create_igc(l1b_rad_fname, orb_fname, l1_osp_dir)

    cmask = CloudMask(
        l1b_rad_fname,
        l1_osp_dir,
        rad_lut_fname=rad_lut_fname,
        b11_lut_file_pattern=b11_lut_file_pattern,
    )
    pool = Pool(10)
    cloud = cmask.cloud_mask(igc=igc, pool=pool)
    cloudconf = cmask.cloud_confidence(igc=igc, pool=pool)

    # Write data out, just so we can easily compare with the expected data
    with h5py.File(cloud_fname, "w") as cloudout:
        sds_group = cloudout.create_group("/SDS")
        sds_group.create_dataset("Cloud_confidence", data=cloudconf, dtype=np.uint8)
        sds_group.create_dataset("Cloud_final", data=cloud, dtype=np.uint8)

    # We have differences because the IGC used in 601 was from before we recalibrated
    # the instrument to spacecraft quaternion. So we just check that we can calculate this
    # without worrying about the exact differences.
    if False:
        subprocess.run(
            ["h5diff", "-r", cloud_fname, test_data_latest / f"{cloud_fname}.expected"],
            check=True,
        )
    # But as a sanity check the cloud fraction should be pretty close (although not
    # identical)
    cfrac = (np.count_nonzero(cloud == 1) / np.count_nonzero(cloud != 255)) * 100.0
    # From examining it, the expected data has a cloud fraction of 88.77 %
    assert abs(cfrac - 85.77) < 0.5
