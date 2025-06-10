# This script is used to test the interpolation code on ECOSTRESS data and benchmark performance.
#
# Steffen Mauceri, JPL, 2025
# Steffen.Mauceri@jpl.nasa.gov



from lib.ecostress_interpolate_new import *
# from test_support import *
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import os
from scipy.special import erfinv
import time
from glob import glob


# TODO: This new flag needs to be added to pipeline
DQI_STRIPE_NOT_INTERPOLATED = 2

# TODO: remove in operational pipeline -------------------------------
fill_value_threshold = -9000 # any value below this is considered a fill value
DQI_GOOD = 0
DQI_INTERPOLATED = 1
DQI_BAD_OR_MISSING = 3
DQI_NOT_SEEN = 4

FILL_VALUE_BAD_OR_MISSING = -9999
FILL_VALUE_STRIPED = -9998
FILL_VALUE_NOT_SEEN = -9997
# ----------------------------------------------------------------------


def ecostress_radiance_to_brightness_temperature(radiance, band):
    """
    Convert ECOSTRESS radiance to brightness temperature using the Planck function.

    Parameters:
    radiance (float or np.array): Measured radiance in W/(m²·sr·µm).
    band (int): ECOSTRESS band number (1-6).

    Returns:
    float or np.array: Brightness temperature in Kelvin.
    """
    band += 1  # Convert from 0-based to 1-based indexing

    # Central wavelengths for each ECOSTRESS band in meters
    ECOSTRESS_WAVELENGTHS = {
        1: 8.285e-6,  # 8.285 µm (unavailable after May 15, 2019)
        2: 8.785e-6,  # 8.785 µm
        3: 9.060e-6,  # 9.060 µm (unavailable after May 15, 2019)
        4: 10.522e-6, # 10.522 µm
        5: 12.001e-6  # 12.001 µm
    }

    if band not in ECOSTRESS_WAVELENGTHS:
        raise ValueError(f"Invalid ECOSTRESS band: {band}. Choose from {list(ECOSTRESS_WAVELENGTHS.keys())}")

    wavelength = ECOSTRESS_WAVELENGTHS[band]

    # Constants
    h = 6.626e-34  # Planck's constant (J·s)
    c = 3.0e8      # Speed of light (m/s)
    k = 1.381e-23  # Boltzmann's constant (J/K)

    # Convert radiance from W/(m²·sr·µm) to W/(m²·sr·m)
    radiance = radiance * 1e6

    # Compute brightness temperature
    Tb = (h * c) / (k * wavelength * np.log((2 * h * c**2) / (radiance * wavelength**5) + 1))

    return Tb

def ecostress_uq_to_brightness_temperature(uq, base_radiance, band):
    """
    Convert radiance uncertainty to brightness temperature uncertainty by offsetting with a base radiance.

    Parameters:
      uq (float or np.array): Radiance uncertainty in W/(m²·sr·µm).
      base_radiance (float or np.array): Base radiance value (e.g., mean radiance) for the conversion.
      band (int): ECOSTRESS band number (0-based indexing expected).

    Returns:
      float or np.array: Brightness temperature uncertainty in Kelvin.
    """
    T_base = ecostress_radiance_to_brightness_temperature(base_radiance, band)
    T_with_uq = ecostress_radiance_to_brightness_temperature(base_radiance + uq, band)
    return T_with_uq - T_base

def vis_interpolation_results(original_data, interpolated_data, data_quality_original, data_quality, save_dir, convert_to_BT=True ,title="", uq=None, remove_poor_quality=True):
    """ Visualize the original and interpolated scene for each band. Add visualization of UQ if available.
    :param original_data: np.array: The original dataset.
    :param interpolated_data: np.array: The interpolated dataset.
    :param save_dir: str: Directory where the plot will be saved.
    :param convert_to_BT: bool: Convert radiance to brightness temperature.
    :param title: str: Title for the plot.
    :param uq: np.array, optional: Uncertainty quantification data.
    :returns: None
    """

    original_data = np.copy(original_data)
    interpolated_data = np.copy(interpolated_data)

    # Set values to NaN where data quality is bad or not interpolated
    if remove_poor_quality:
        original_data[data_quality_original >= 2] = np.nan
        interpolated_data[data_quality >= 2] = np.nan

    for band in range(5):
        if convert_to_BT:
            # convert radiance to temperature for visualization
            original_data[..., band] = ecostress_radiance_to_brightness_temperature(original_data[..., band], band)
            interpolated_data[..., band] = ecostress_radiance_to_brightness_temperature(interpolated_data[..., band], band)

            if uq is not None:
                uq[..., band] = ecostress_uq_to_brightness_temperature(uq[..., band], interpolated_data[..., band],band)


        # Plot the interpolated dataset vs the original dataset
        # Create a figure with two subplots side by side
        if uq is not None:
            fig, axes = plt.subplots(1, 3, figsize=(21, 7))
        else:
            fig, axes = plt.subplots(1, 2, figsize=(14, 7))  # 1 row, 2 columns

        # Set a title for the whole figure
        fig.suptitle(title, fontsize=16)

        # get vmin and vmax
        if remove_poor_quality:
            vmin = np.nanpercentile(original_data[:, :, band], 2)
            vmax = np.nanpercentile(original_data[:, :, band], 98)
        else:
            original_data_good = original_data.copy()
            original_data_good[data_quality >= 2] = np.nan
            vmin = np.nanpercentile(original_data_good[:, :, band], 2)
            vmax = np.nanpercentile(original_data_good[:, :, band], 98)

        # Plot the original dataset
        cmap = plt.get_cmap('viridis').copy()
        cmap.set_bad('grey')

        im1 = axes[0].imshow(original_data[:, :, band], vmin=vmin, vmax=vmax, cmap=cmap)
        axes[0].set_title(f"Original Data - Band {band + 1}")
        axes[0].axis('off')  # Hide axis ticks

        # Add a colorbar for the original data
        cbar1 = fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)
        if convert_to_BT:
            cbar1.set_label('Brightness Temperature (K)')
        else:
            cbar1.set_label('Radiance (W/(m²·sr·µm))')

        # Plot the interpolated dataset
        im2 = axes[1].imshow(interpolated_data[:, :, band], vmin=vmin, vmax=vmax, cmap=cmap)
        axes[1].set_title(f"Interpolated Data - Band {band + 1}")
        axes[1].axis('off')  # Hide axis ticks

        # Add a colorbar for the interpolated data
        cbar2 = fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)
        if convert_to_BT:
            cbar2.set_label('Brightness Temperature (K)')
        else:
            cbar2.set_label('Radiance (W/(m²·sr·µm))')

        if uq is not None:
            cmap = plt.get_cmap('Reds').copy()
            cmap.set_bad('grey')
            uq_non_zero = uq[:, :, band][uq[:, :, band] > 0]
            vmin = np.nanpercentile(uq_non_zero, 2)
            vmax = np.nanpercentile(uq_non_zero, 98)
            # Plot the uncertainty
            # set uq to nan if it is zero for visualization
            uq_nan = np.copy(uq)
            uq_nan[uq == 0] = np.nan
            im3 = axes[2].imshow(uq_nan[:, :, band], vmin=vmin, vmax=vmax, cmap=cmap)
            axes[2].set_title(f"Interpolation Uncertainty - Band {band + 1}")
            axes[2].axis('off')  # Hide axis ticks

            # Add a colorbar for the uncertainty
            cbar3 = fig.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04)
            if convert_to_BT:
                cbar3.set_label('Uncertainty (K)')
            else:
                cbar3.set_label('Uncertainty (W/(m²·sr·µm))')

        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f"{title}_band_{band + 1}.png"), dpi=300)
        plt.close()

def vis_data_quality(data_quality, save_dir,title=""):
    """ Visualize the data quality for each band.
    :param data_quality: np.array, 3D array containing data quality information for each band.
    :param save_dir: str, Directory where the plot will be saved.
    :param title: str, Title for the plot.
    :return: None
    """

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()  # Flatten the axes array for correct indexing
    fig.suptitle(title, fontsize=16)
    # get vmin and vmax
    vmin = 0
    vmax = 3
    # reverse the color map and only preserve the first 3 colors
    cmap = ListedColormap(plt.get_cmap('Set1').colors[:4][::-1])

    for band in range(5):
        im1 = axes[band].imshow(data_quality[:, :, band], vmin=vmin, vmax=vmax, cmap=cmap)
        axes[band].set_title(f"Data Quality - Band {band + 1}")
        axes[band].axis('off')  # Hide axis ticks
        cbar = fig.colorbar(im1, ax=axes[band], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"{title}.png"), dpi=300)
    plt.close()

def load_data(data_path, size=None):
    """Load the ECOSTRESS dataset and data quality information from an HDF5 file.
    applies the data quality mask to the dataset.

    Parameters:
    data_path (str): Path to HDF5 file.
    size (int, optional): If provided, reduce the size of the dataset for testing/visualization.

    Returns:
    tuple: A tuple containing:
        - dataset (np.array): The loaded dataset array.
        - data_quality (np.array): The data quality array.
    """
    # Load the HDF5 file)
    f = h5py.File(data_path)

    # Create dataset array
    # dataset = np.zeros((*f["/SDS/radiance_1"].shape, 5))
    dataset = np.zeros((*f["/Radiance/radiance_1"].shape, 5))
    data_quality = np.zeros(dataset.shape)

    # Load all bands and their quality indicators
    for b in range(5):
        # dataset[:, :, b] = f["/SDS/radiance_%d" % (b + 1)]
        # data_quality[:, :, b] = f["/SDS/data_quality_%d" % (b + 1)]
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

    if size is not None:
        # reduce size for testing / visualization
        dataset = dataset[:size, :size, :]
        data_quality = data_quality[:size, :size, :]

    return dataset, data_quality

def expected_calibration_error(mean_preds, std_preds, test_y, save_dir, title=""):
    """
    Compute a coverage-based calibration curve and ECE for the ensemble predictions.

    1) We assume a Gaussian predictive distribution for each pixel: N(mean_preds, std_preds^2).
    2) We define a set of coverage levels (e.g., 0.05, 0.15, ..., 0.95).
    3) For each coverage level c, we compute k such that c = erf(k / sqrt(2)).
       This means we consider the interval [mean_preds - k*std_preds, mean_preds + k*std_preds].
    4) We measure the fraction of ground-truth points test_y that fall within that interval.
    5) We plot the observed coverage vs. the nominal coverage.
    6) We define ECE as the mean absolute deviation between nominal (ideal) coverage and observed coverage.
    """

    # Remove NaNs if needed
    valid_mask = ~np.isnan(mean_preds)

    pred_mean = mean_preds[valid_mask].flatten()
    pred_std = std_preds[valid_mask].flatten()
    y_true = test_y[valid_mask].flatten()

    # Coverage levels (nominal coverage)
    coverage_levels = np.linspace(0.05, 0.95, 10)
    observed_coverage = np.zeros_like(coverage_levels)

    # Compute observed coverage for each nominal coverage level
    for i, c in enumerate(coverage_levels):
        # Solve c = erf(k / sqrt(2)) -> k = sqrt(2) * erfinv(c)
        k = np.sqrt(2) * erfinv(c)

        # Lower and upper bounds of the predictive interval
        lower = pred_mean - k * pred_std
        upper = pred_mean + k * pred_std

        # Fraction of y_true that lies in [lower, upper]
        in_interval = (y_true >= lower) & (y_true <= upper)
        observed_coverage[i] = np.mean(in_interval)

    # add 0 and 1 to the coverage levels and observed coverage to make the curve start and end at 0 and 1
    coverage_levels = np.concatenate(([0], coverage_levels, [1]))
    observed_coverage = np.concatenate(([0], observed_coverage, [1]))

    # Compute ECE as the mean absolute difference
    ece = np.mean(np.abs(observed_coverage - coverage_levels))

    # Plot the coverage calibration curve
    plt.figure(figsize=(6, 6))
    plt.plot(coverage_levels, observed_coverage, marker='o', label='Observed Coverage')
    # Perfect calibration line
    plt.plot([0, 1], [0, 1], 'r--', label='Ideal')
    plt.xlabel('Expected Coverage')
    plt.ylabel('Observed Coverage')
    plt.title('Coverage Calibration Curve')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(save_dir, f"{title}_coverage_calibration_curve.png"), dpi=300)
    plt.close()

    return ece

def scatter_plot_true_vs_predicted(pred_data, true_data,  bands_to_process,save_dir, unit_label, title=""):

    fig, axs = plt.subplots(1, len(bands_to_process), figsize=(5 * len(bands_to_process), 5))
    fig.suptitle(title, fontsize=16)

    i = 0
    for band in bands_to_process:
        # Flatten the arrays and remove NaNs
        true_band = true_data[:, :, band].flatten()
        pred_band = pred_data[:, :, band].flatten()
        mask = ~np.isnan(true_band) & ~np.isnan(pred_band)
        true_band = true_band[mask]
        pred_band = pred_band[mask]

        # subsample if we have too many points
        if len(true_band) > 10000:
            idx = np.random.choice(len(true_band), 10000, replace=False)
            true_band = true_band[idx]
            pred_band = pred_band[idx]

        # Scatter plot of true vs. predicted values
        axs[i].scatter(true_band, pred_band, alpha=0.1, color='blue', label="Data", s=2, marker='.')

        # Perform a linear fit
        slope, intercept = np.polyfit(true_band, pred_band, 1)
        fit_func = np.poly1d([slope, intercept])

        # Compute fitted values and R²
        fitted = fit_func(true_band)
        ss_res = np.sum((pred_band - fitted) ** 2)
        ss_tot = np.sum((pred_band - np.mean(pred_band)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

        # Plot the fit line (sort the values for a smooth line)
        sorted_idx = np.argsort(true_band)
        sorted_true = true_band[sorted_idx]
        sorted_fit = fit_func(sorted_true)
        axs[i].plot(sorted_true, sorted_fit, color='red',
                       label=f"Fit: slope={slope:.2f}, intercept={intercept:.2f}")

        # Set subplot title including R²
        axs[i].set_title(f"Band {band + 1} (R²={r2:.2f})")
        axs[i].set_xlabel("True " + unit_label)
        axs[i].set_ylabel("Interpolated " + unit_label)

        # make sure x and y lim are the same. set to 1 and 99 percentile
        lim = np.nanpercentile(true_band, [1, 99])
        axs[i].set_xlim(lim)
        axs[i].set_ylim(lim)
        axs[i].legend()

        i+=1

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"{title}_scatter_plot.png"), dpi=300)
    plt.close()

def plot_combined_histogram(combined_errors, save_dir, unit_label="(K)", title="Combined Interpolation Errors by Band", filename="combined_interpolation_error_histogram.png"):
    plt.figure(figsize=(8, 6))
    aggregated_rmse_dict = {}
    for band, error_list in combined_errors.items():
        all_errors = np.concatenate(error_list)
        aggregated_rmse = np.sqrt(np.mean(all_errors ** 2))
        aggregated_rmse_dict[band] = aggregated_rmse
        print(f"Aggregated RMSE for Band {band}: {aggregated_rmse:.3f}")
        plt.hist(all_errors, bins=50, alpha=0.5, label=f"Band {band}", density=True, histtype='step')
    plt.axvline(0, color='black', linestyle='--', linewidth=1)
    plt.xlabel("Interpolation Error " + unit_label)
    plt.ylabel("Probability Density")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, filename), dpi=300)
    plt.close()

    return aggregated_rmse_dict

def benchmark_interpolate(save_dir, data_path, convert_to_BT=False, size=None, epochs=25, batch_size=32, n_samples=100000):
    """
    Benchmark the interpolation code on the given data path. Compared to run_interpolate,
    this function will remove good data so we can quantify interpolation errors.

    Parameters:
        save_dir (str): Directory where outputs (plots/logs) will be saved.
        data (str): Path to the HDF5 file.
        convert_to_BT (bool): If True, compute errors in brightness temperature (using
                              ecostress_radiance_to_brightness_temperature) instead of radiance.
    """



    scene = data_path.split("/")[-1].split(".")[0]
    # Load the dataset and data quality information
    dataset, data_quality = load_data(data_path, size=size)

    # get number of bands by checking how many bands are not all bad (data_quality == BAD_OR_MISSING)
    N_BANDS = int(np.sum(np.any(data_quality != DQI_BAD_OR_MISSING, axis=(0, 1))))
    print(f"N_BANDS: {N_BANDS}")

    if N_BANDS == 3:
        bands_to_process = [1, 3, 4]
    elif N_BANDS == 5:
        bands_to_process = [0, 1, 2, 3, 4]
    else:
        raise ValueError(f"Invalid number of bands: {N_BANDS}. Choose 3 or 5.")


    # Make a copy of the original dataset for visualization later
    dataset_original = np.copy(dataset)
    data_quality_original = np.copy(data_quality)

    interpolator = EcostressAeDeepEnsembleInterpolate(n_bands=N_BANDS)

    data_quality = interpolator.find_horizontal_stripes(dataset, data_quality)
    # dataset[data_quality == DQI_STRIPE_NOT_INTERPOLATED] = FILL_VALUE_STRIPED  # remove the identified stripes

    vis_data_quality(data_quality, save_dir, title=f"Data Quality before processing: {scene}")

    # # visualize the identified stripes
    # vis_interpolation_results(dataset_original, dataset, data_quality_original, data_quality, save_dir, convert_to_BT=convert_to_BT,
    #                           title=f"Stripe Identifier: {scene}")

    # Remove good data so we can later quantify interpolation errors:
    # randomly add stripes of varying width
    data_testing = np.zeros_like(data_quality, dtype=bool)
    widths = [1, 1,1, 2, 2, 2,2, 8, 8]
    edge = 50 # avoid edges. Important for missing data on edges
    for width in widths:
        # choose a random starting row
        row = np.random.randint(1, dataset.shape[0] - 10)
        # choose up to 3 random bands if we have 5 bands
        n_bands_choice = np.random.randint(1, N_BANDS-1) # high is not included in random choice
        bands = np.random.choice(bands_to_process, n_bands_choice, replace=False)

        # check that the stripe does not overlap with existing bad data
        i = 0
        while np.any(data_quality[row:row + 10, edge:-edge, bands_to_process] > 0):
            row = np.random.randint(1, dataset.shape[0] - 10)
            i += 1
            if i > 100:
                print("Could not find a good stripe location. Exiting.")
                return

        # set the stripe to FILL_VALUE_STRIPED
        dataset[row:row + width, edge:-edge, bands] = FILL_VALUE_STRIPED
        data_quality[row:row + width, edge:-edge, bands] = DQI_STRIPE_NOT_INTERPOLATED
        data_testing[row:row + width, edge:-edge, bands] = True

    vis_data_quality(data_quality, save_dir, title=f"Data Quality with Removed Test Data: {scene}")


    # Train the model and perform interpolation
    print("Starting model training")
    tik = time.time()
    interpolator.train(dataset, data_quality, epochs=epochs, batch_size=batch_size, n_samples=n_samples, validate=True)
    if size is None:
        print(f"Training took {time.time() - tik:.2f} seconds.")

    print("Performing interpolation")
    tik = time.time()
    interpolated_dataset, interpolation_uncertainty, data_quality = interpolator.interpolate_missing(dataset.copy(), data_quality)
    # visualize the results
    vis_interpolation_results(dataset_original, interpolated_dataset, data_quality_original, data_quality, save_dir, convert_to_BT=convert_to_BT,
                              uq=interpolation_uncertainty, title=f"AE Ensemble Interpolator: {scene}")
    if size is None:
        print(f"Interpolation took {time.time() - tik:.2f} seconds.")

    vis_data_quality(data_quality, save_dir, title=f"Data Quality after Interpolation: {scene}")

    # If brightness temperature output is requested, convert both original and interpolated data.
    # Note: vis_interpolation_results will also convert if convert_to_BT is True, but we need
    # to convert here for error analysis.
    if convert_to_BT:
        unit_label = "(Brightness Temperature, K)"
        for band in range(5):
            dataset_original[..., band] = ecostress_radiance_to_brightness_temperature(dataset_original[..., band], band)
            dataset[..., band] = ecostress_radiance_to_brightness_temperature(dataset[..., band], band)
            interpolation_uncertainty[..., band] = ecostress_uq_to_brightness_temperature(interpolation_uncertainty[..., band], interpolated_dataset[..., band], band)
            interpolated_dataset[..., band] = ecostress_radiance_to_brightness_temperature(interpolated_dataset[..., band], band)
    else:
        unit_label = "(Radiance, W/(m²·sr·µm))"

    # Quantify interpolation errors by band and count available test pixels. *************************************
    overall_errors = []
    scene_band_errors = {}
    scene_rmse_by_band = {}
    error_file = os.path.join(save_dir, f"interpolation_errors_{scene}.txt")
    with open(error_file, "w") as f:
        f.write("Interpolation Errors by Band:\n")
        print("\nInterpolation Errors by Band:")
        mask_all = (data_testing[:, :, :] & (data_quality[:, :, :] == DQI_INTERPOLATED))
        for band in bands_to_process:
            mask_band = mask_all[:, :, band]
            if np.any(mask_band):
                # Calculate error on the selected pixels
                # need to use dataset_original since it contains true values before test stripes were added
                errors = dataset_original[:, :, band][mask_band] - interpolated_dataset[:, :, band][mask_band]
                rmse_band = np.sqrt(np.mean(errors ** 2))
                scene_band_errors[band + 1] = errors  # Store errors for this scene and band
                scene_rmse_by_band[band + 1] = rmse_band # Store RMSE for this scene and band
                n_points = np.sum(mask_band)
                line = (f"Band {band + 1}: {n_points} test pixels, RMSE: {rmse_band:.3f} {unit_label}")
                print(line)
                f.write(line + "\n")
                overall_errors.append((band + 1, errors))
            else:
                line = f"Band {band + 1}: No test pixels available."
                print(line)
                f.write(line + "\n")

    # Compute overall RMSE across all bands with test pixels
    if overall_errors:
        all_errors = np.concatenate([err for (_, err) in overall_errors])
        overall_rmse = np.sqrt(np.mean(all_errors ** 2))
        print(f"\nOverall RMSE: {overall_rmse:.3f}")
        with open(error_file, "a") as f:
            f.write(f"\nOverall RMSE: {overall_rmse:.3f}")
    else:
        print("\nNo interpolation errors to compute overall RMSE.")


    # Plot a histogram of errors for each band. *********************************************************************
    plt.figure(figsize=(6, 4))
    for band, errors in overall_errors:
        plt.hist(errors, bins=50, alpha=0.5, label=f"Band {band}", density=True, histtype='step')
    # add a vertical line at 0
    plt.axvline(0, color='black', linestyle='--', linewidth=1)
    plt.xlabel("Interpolation Error " + unit_label)
    plt.ylabel("Probability Density")
    plt.title("Interpolation Errors by Band")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"interpolation_error_histogram_{scene}.png"), dpi=300)
    plt.close()


    # Quantify interpolation errors by number of available good bands. ******************************************
    # Group errors by number of valid bands
    error_groups = {}  # keys: number of other valid bands (0 to num_bands-1)
    # Compute for every pixel (i, j) the total number of valid bands.
    n_band_interpolated = np.sum(mask_all, axis=2)  # shape: (height, width)

    for b in bands_to_process:
        # Get the boolean mask for the current band
        band_mask = mask_all[:, :, b]
        # Compute the errors at pixels where the current band was a test pixel
        band_errors = (dataset_original[:, :, b] - interpolated_dataset[:, :, b])[band_mask]
        # For those pixels, count how many other bands had valid data.
        # (Subtract 1 because the current band is included in the valid count.)
        other_valid = N_BANDS - n_band_interpolated[band_mask]
        for err, n_other in zip(band_errors, other_valid):
            error_groups.setdefault(n_other, []).append(err)

    # Plot histogram for each group
    plt.figure(figsize=(8, 6))
    for n_other, errs in sorted(error_groups.items()):
        plt.hist(errs, bins=50, alpha=0.5, label=f"{n_other} valid bands", density=True, histtype='step')
    plt.axvline(0, color='black', linestyle='--', linewidth=1)
    plt.xlabel("Interpolation Error " + unit_label)
    plt.ylabel("Probability Density")
    plt.title("Interpolation Errors Grouped by Number of Good Bands")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f"interpolation_error_histogram_by_valid_bands_{scene}.png"), dpi=300)
    plt.close()

    # only keep the test pixels
    dataset_masked = np.copy(dataset_original) # need to use dataset_original since it contains true values before test stripes were added
    interpolated_masked = np.copy(interpolated_dataset)
    uncertainty_masked = np.copy(interpolation_uncertainty)

    dataset_masked[~mask_all] = np.nan
    interpolated_masked[~mask_all] = np.nan
    uncertainty_masked[~mask_all] = np.nan

    # Calculate expected calibration error (ECE) for the ensemble predictions *************************************
    ece = expected_calibration_error(interpolated_masked, uncertainty_masked, dataset_masked, save_dir, title=scene)
    print(f"Expected calibration error: {ece:.3f}")
    with open(error_file, "a") as f:
        f.write(f"\nExpected Calibration Error: {ece:.3f}")

    # Make a scatter plot of true vs predicted for each band to visualize the interpolation errors *******************
    scatter_plot_true_vs_predicted(interpolated_masked, dataset_masked, bands_to_process, save_dir, unit_label,  title=scene)

    print(f"Benchmarking complete for {scene}")
    return overall_rmse, scene_band_errors, scene_rmse_by_band

def run_interpolate(save_dir, data_path, convert_to_BT=False, size=None, epochs=25, batch_size=32, n_samples=100000):
    '''Run the interpolation and visualization code on the given data path'''

    scene = data_path.split("/")[-1].split(".")[0]
    # Load the dataset and data quality information
    dataset, data_quality = load_data(data_path, size=size)

    # Make a copy of the original dataset for visualization later
    dataset_original = np.copy(dataset) # no stripes will be added to this dataset
    data_quality_original = np.copy(data_quality)

    # get number of bands by checking how many bands are not all bad (data_quality == BAD_OR_MISSING)
    N_BANDS = int(np.sum(np.any(data_quality != DQI_BAD_OR_MISSING, axis=(0, 1))))
    print(f"N_BANDS: {N_BANDS}")

    # Create an instance of the EcostressAeDeepEnsembleInterpolate class
    interpolator = EcostressAeDeepEnsembleInterpolate(n_bands=N_BANDS)


    vis_data_quality(data_quality, save_dir, title=f"Before processing: {scene}")
    # update data quality mask
    data_quality = interpolator.find_horizontal_stripes(dataset, data_quality)


    # check if we have any negative radiances with a good DQI
    if np.any((dataset < 0) & (data_quality == DQI_GOOD)):
        print(f"Found negative radiances with good DQI in {scene}. Setting to FILL_VALUE_BAD_OR_MISSING")
        # set any negative radiances to FILL_VALUE_BAD_OR_MISSING
        data_quality[dataset < 0] = DQI_BAD_OR_MISSING
        dataset[dataset < 0] = FILL_VALUE_BAD_OR_MISSING

    vis_data_quality(data_quality, save_dir, title=f"Stripes Identified: {scene}")

    # Train the model and perform interpolation
    print("Starting model training")
    interpolator.train(dataset, data_quality, epochs=epochs, batch_size=batch_size, n_samples=n_samples, validate = True)

    print("Performing interpolation")
    interpolated_dataset, interpolation_uncertainty, data_quality = interpolator.interpolate_missing(dataset, data_quality)
    vis_interpolation_results(dataset_original, interpolated_dataset, data_quality_original, data_quality,
                              save_dir, convert_to_BT=convert_to_BT, uq = interpolation_uncertainty, title=f"AE Ensemble Interpolator: {scene}")
    print(f"Interpolation complete for {scene}")
    vis_data_quality(data_quality, save_dir, title=f"Final DQ: {scene}")



#TODO:
# clean up the code

save_dir = "/Users/smauceri/Projects/ECOSTRESS/code/plots/"  # Directory for test outputs/logs
data_path = "/Users/smauceri/Projects/ECOSTRESS/data/5_band/ECOSTRESS_L1B_RAD*.h5"         # Path to directory containing HDF5 file

Benchmark = False # Set to True to run benchmarking mode otherwise we just run the interpolation
convert_to_BT = True
size = None

save_dir_unit = "BT" if convert_to_BT else "Rad" # Append to save_dir to indicate BT or radiance
save_dir_model = "AeDeepEnsemble"  # Append to save_dir to indicate the model used
save_dir_mode = "Bench" if Benchmark else "Interp"  # Append to save_dir to indicate benchmark or test mode
save_dir_bands = "3_band" if '3_band' in data_path else "5_band"  # Append to save_dir to indicate 3-band or 5-band

save_dir = os.path.join(save_dir, f"{save_dir_model}_{save_dir_mode}_{save_dir_unit}_{save_dir_bands}_{size}")


# make save directory if it does not exist
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# get all scene files
files = glob(data_path)

# **Aggregate metrics across scenes**
combined_errors = {}  # key: band, value: list of error arrays from each scene
combined_rmse = {}    # key: band, value: list of RMSE values from each scene
for file_path in files:
    if Benchmark:
        overall_rmse, scene_errors, scene_rmse = (
            benchmark_interpolate(save_dir, file_path, convert_to_BT=convert_to_BT, size = size))
    else:
        run_interpolate(save_dir, file_path, convert_to_BT=convert_to_BT, size = size)

if Benchmark:
    for band, errors in scene_errors.items():
        combined_errors.setdefault(band, []).append(errors)
    for band, rmse_value in scene_rmse.items():
        combined_rmse.setdefault(band, []).append(rmse_value)

    # Plot combined histogram and compute aggregated RMSE per band
    if convert_to_BT:
        unit_label = "(Brightness Temperature, K)"
    else:
        unit_label = "(Radiance, W/(m²·sr·µm))"
    aggregated_rmse = plot_combined_histogram(combined_errors, save_dir, unit_label=unit_label)
    # write aggregated RMSE to file
    with open(os.path.join(save_dir, "aggregated_rmse.txt"), "w") as f:
        f.write("Aggregated RMSE by Band:\n")
        for band, rmse_value in aggregated_rmse.items():
            f.write(f"Band {band}: {rmse_value:.3f}\n")

print("Done >>>")