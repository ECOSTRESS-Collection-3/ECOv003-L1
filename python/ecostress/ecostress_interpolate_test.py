from lib.ecostress_interpolate_new import *
# from test_support import *
import h5py
import numpy as np



#@slow
def test_interpolate(isolated_dir, test_data):

    # TODO: This new flag needs to the overall data pipeline
    DQI_STRIPE_NOT_INTERPOLATED = 2

    # TODO: remove in operational pipeline -------------------------------
    fill_value_threshold = -9000  # any value below this is considered a fill value
    DQI_GOOD = 0
    DQI_INTERPOLATED = 1
    DQI_BAD_OR_MISSING = 3
    DQI_NOT_SEEN = 4

    FILL_VALUE_BAD_OR_MISSING = -9999
    FILL_VALUE_STRIPED = -9998
    FILL_VALUE_NOT_SEEN = -9997
    # ----------------------------------------------------------------------


    def load_data(data_path):
        """Load the ECOSTRESS dataset and data quality information from an HDF5 file.
        applies the data quality mask to the dataset.

        Parameters:
        data_path (str): Path to HDF5 file.

        Returns:
        tuple: A tuple containing:
            - dataset (np.array): The loaded dataset array.
            - data_quality (np.array): The data quality array.
        """
        # Load the HDF5 file)
        f = h5py.File(data_path)

        # Create dataset array
        dataset = np.zeros((*f["/Radiance/radiance_1"].shape, 5))
        data_quality = np.zeros(dataset.shape)

        # Load all bands and their quality indicators
        for b in range(5):
            dataset[:, :, b] = f["/Radiance/radiance_%d" % (b + 1)]
            data_quality[:, :, b] = f["/Radiance/data_quality_%d" % (b + 1)]

        # make sure we remove the previously interpolated data
        dataset[data_quality == DQI_INTERPOLATED] = FILL_VALUE_STRIPED

        # start a new data quality mask
        data_quality = np.zeros(dataset.shape)

        # make data_quality array to generate dqi that would be seen by interpolator
        data_quality[dataset == FILL_VALUE_NOT_SEEN] = DQI_NOT_SEEN
        data_quality[dataset == FILL_VALUE_STRIPED] = DQI_STRIPE_NOT_INTERPOLATED
        data_quality[dataset == FILL_VALUE_BAD_OR_MISSING] = DQI_BAD_OR_MISSING

        print("Data loaded successfully")

        return dataset, data_quality

    def run_interpolate(data_path, epochs=25, batch_size=32, n_samples=100000):
        '''Run the interpolation and visualization code on the given data path.

        Parameters:
        data_path (str): Path to the HDF5 file containing the dataset.
        epochs (int, optional): Number of epochs for training the model.
        batch_size (int, optional): Batch size for training the model.
        n_samples (int, optional): Number of samples for training the model.
        '''


        scene = data_path.split("/")[-1].split(".")[0]
        # Load the dataset and data quality information
        dataset, data_quality = load_data(data_path)

        # remove band 2 pixel for testing
        xy_pixel = 100
        band_pixel = 1
        test_pixel = dataset[xy_pixel,xy_pixel,band_pixel]
        data_quality[xy_pixel,xy_pixel,band_pixel] = DQI_BAD_OR_MISSING

        # get number of bands by checking how many bands are not all bad (data_quality == BAD_OR_MISSING)
        N_BANDS = int(np.sum(np.any(data_quality != DQI_BAD_OR_MISSING, axis=(0, 1))))
        print(f"N_BANDS: {N_BANDS}")




        # START of minimal example of how to use the EcostressAeDeepEnsembleInterpolate class ----------------------------------
        # Create an instance of the EcostressAeDeepEnsembleInterpolate class
        interpolator = EcostressAeDeepEnsembleInterpolate(n_bands=N_BANDS)

        # identify horizontal stripes and update data quality mask
        data_quality = interpolator.find_horizontal_stripes(dataset, data_quality)

        # check if we have any negative radiances with a good DQI
        if np.any((dataset < 0) & (data_quality == DQI_GOOD)):
            print(f"Found negative radiances with good DQI in {scene}. Setting to FILL_VALUE_BAD_OR_MISSING")
            # set any negative radiances to FILL_VALUE_BAD_OR_MISSING
            data_quality[dataset < 0] = DQI_BAD_OR_MISSING
            dataset[dataset < 0] = FILL_VALUE_BAD_OR_MISSING

        # Train the model and perform interpolation
        print("Starting model training")
        interpolator.train(dataset, data_quality, epochs=epochs, batch_size=batch_size, n_samples=n_samples,
                           validate=True, validate_threshold=0.2)

        print("Performing interpolation")
        interpolated_dataset, interpolation_uncertainty, data_quality = interpolator.interpolate_missing(dataset, data_quality)
        # END of minimal example --------------------------------------------------------------------------------------




        # perform addiitonal checks ---------------------------------------------------------------------------------
        test_pixel_interpolated = interpolated_dataset[xy_pixel, xy_pixel, band_pixel]
        test_pixel_error = np.abs(test_pixel - test_pixel_interpolated)

        assert test_pixel_error < 1, f"Test pixel error is too high: {test_pixel_error}"
        # check that the interpolated pixel is not equal to the original pixel
        assert test_pixel_interpolated != test_pixel, "Test pixel interpolated value is equal to original value"
        # test that data quality flag has been updated for test pixel
        assert data_quality[xy_pixel, xy_pixel, band_pixel] == DQI_INTERPOLATED, "Data quality flag not updated for test pixel"


        # make sure the output is the same shape as the input
        assert interpolated_dataset.shape == dataset.shape, "Interpolated dataset shape does not match input dataset shape"
        # make sure the values changed
        assert np.any(interpolated_dataset != dataset), "Interpolated dataset is the same as input dataset"


    data_path_3_band = test_data + "ECOSTRESS_L1B_RAD_16147_025_20210512T032304_0601_01.h5"
    data_path_5_band = test_data + "ECOSTRESS_L1B_RAD_35950_006_20241108T002252_0601_01.h5"

    # get all scene files
    files = [data_path_3_band, data_path_5_band]

    for file_path in files:
        run_interpolate(file_path)


isolated_dir = "../sandbox/tests/isolated_output"  # Directory for test outputs/logs
#test_data = "/Users/smauceri/Projects/ECOSTRESS/data/test_data/"         # Path to directory containing HDF5 file

test_interpolate(isolated_dir, test_data)