from ecostress import BrowseImage
import geocal
import h5py


def test_browse_image(isolated_dir, test_data_latest):
    l1ct_fname = (
        test_data_latest
        / "ECOv002_L1CG_RAD_03663_001_20190227T101222_0100_01.h5.expected"
    )
    fin = h5py.File(l1ct_fname, "r")
    data_in = [
        fin["/HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields/radiance_5"][:, :],
        fin["/HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields/radiance_4"][:, :],
        fin["/HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields/radiance_2"][:, :],
    ]
    minfo = geocal.GdalRasterImage(
        f'HDF5:"{l1ct_fname}"://HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data_Fields/radiance_5'
    ).map_info
    bimg = BrowseImage(data_in, minfo, isolated_dir)
    print(bimg)
