from __future__ import annotations
import numpy as np
from ecostress_swig import (  # type: ignore
    DQI_INTERPOLATED,
    DQI_STRIPE_NOT_INTERPOLATED,
    DQI_GOOD,
    DQI_NOT_SEEN,
    fill_value_threshold,
)
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    import tensorflow as tf  # type: ignore


def _find_horizontal_stripes(
    dataset: np.ndarray, data_quality: np.ndarray, n_bands: int, threshold: int = 5
) -> np.ndarray:
    """analyzes ECOSTRESS scene and looks for missing, high, or
    low horizontal stripes that are not identified in data_quality
    mask. Currently constrained to identifying horizontal stripes
    with a width of 1 to 2 px.  Could be readily modified to
    identify wider stripes if needed.

    :param dataset: input dataset (ECOSTRESS scene)
    :param data_quality: data quality mask
    :param n_bands: number of bands in the dataset
    :param threshold: threshold for identifying stripes (defined as multiple of MAD)

    :return: updated data quality mask

    """

    if n_bands == 3:
        bands_to_process = [1, 3, 4]
    elif n_bands == 5:
        bands_to_process = [0, 1, 2, 3, 4]
    else:
        raise ValueError("n_bands must be 3 or 5")

    # make a copy of the dataset so we do not modify the original
    dataset = dataset.copy()

    # remove bad
    dataset[dataset < fill_value_threshold] = np.nan

    for band in bands_to_process:
        band_data = dataset[:, :, band]

        # Compute row-wise differences to detect rapid intensity changes
        row_diff = np.abs(np.diff(band_data, axis=0))
        row_diff = np.concatenate([np.zeros((1, row_diff.shape[1])), row_diff], axis=0)

        # First summarize the pixel-wise differences for each row using the mean
        row_diff_summary = np.nanmean(row_diff, axis=1)

        # set nan to 0. That happens when the row is all nan
        row_diff_summary[np.isnan(row_diff_summary)] = 0

        # Compute median absolute deviation (MAD) for robust thresholding
        mad = np.median(np.abs(row_diff_summary - np.median(row_diff_summary)))

        # Identify stripe candidates where differences exceed threshold * MAD
        stripe_row = row_diff_summary > np.median(row_diff_summary) + threshold * mad

        # make sure we have a stripe rather than a plateu.
        # Need to have identified two stripes in close proximity
        for i in range(1, len(stripe_row) - 2):
            if stripe_row[i]:
                # check if there is a stripe in the next 2 rows
                if not stripe_row[i + 1] and not stripe_row[i + 2]:
                    stripe_row[i] = False
                else:
                    # set the next stripe to true in case it is not already True
                    stripe_row[i + 1] = True

        # set stripe to 1 if not already identified
        data_quality[stripe_row, :, band] = DQI_STRIPE_NOT_INTERPOLATED
        # Debug print removed

    return data_quality


class EcostressAeDeepEnsembleInterpolate(object):
    """Class to interpolate missing data in ECOSTRESS scenes.
    Steffen Mauceri, JPL, 2025
    Steffen.Mauceri@jpl.nasa.gov

    Notes:
    replaces the earlier ecostress_interpolate.py
    Compared to earlier version this routine uses:
     - Autoencoder-based interpolation model and provides uncertainties
     - TF 2.x, the Keras API, Adam optimizer, NLL loss function
     - errors are calculated on a test set, not the training set.
     - scanlines can be missing in any band and will be interpolated if at least 2 bands are good.
     - horizontal stripes are identified and interpolated if at least 2 bands are good.
     - model takes no spatial information into account.
    """

    def __init__(
        self,
        grid_size: int = 1,
        n_bands: int = 5,
        latent_dim: int = 16,
        encoder_layers: list[int] = [32],
        decoder_layers: list[int] = [32],
        activation: str = "elu",
        fill_value_threshold: float = fill_value_threshold,
        seed: int = 1234,
        n_ensemble: int = 3,
        n_good_bands_required: int = 2,
        band_weights: list[float] = [
            3.0,
            0.1,
            0.5,
            1.0,
            3.0,
        ],  # Weights for each band in loss function
        verbose: bool = True,
    ) -> None:
        """
        Deep Ensemble version of the autoencoder-based interpolation model.

        Args:
            grid_size: Size of the spatial grid to consider for each prediction
            n_bands: Number of bands in the data
            latent_dim: Dimension of the latent space
            encoder_layers: List of layer sizes for the encoder
            decoder_layers: List of layer sizes for the decoder
            activation: Activation function to use
            fill_value_threshold: Threshold for identifying fill values
            seed: Random seed for reproducibility
            n_ensemble: Number of models to include in the ensemble
            n_good_bands_required: Minimum number of good bands required for interpolation
            band_weights: Weights for each band in the loss function. Higher weights emphasize that band's error more.
            verbose: Whether to print verbose output
        """
        self.grid_size = grid_size
        self.n_bands = n_bands
        self.latent_dim = latent_dim
        self.encoder_layers = encoder_layers
        self.decoder_layers = decoder_layers
        self.activation = activation
        self.fill_value_threshold = fill_value_threshold
        self.seed = seed
        self.n_ensemble = n_ensemble
        self.n_good_bands_required = n_good_bands_required
        self.band_weights = band_weights
        self.verbose = verbose

        # Will store normalization parameters
        self.mu: np.ndarray | None = None
        self.sigma: np.ndarray | None = None

        # Each member of the ensemble is a separate model
        self.models = [self._build_model(i) for i in range(n_ensemble)]

    def find_horizontal_stripes(
        self,
        dataset: np.ndarray,
        data_quality: np.ndarray,
        threshold: int = 5,
    ) -> np.ndarray:
        """analyzes ECOSTRESS scene and looks for missing, high, or
        low horizontal stripes that are not identified in data_quality
        mask. Currently constrained to identifying horizontal stripes
        with a width of 1 to 2 px.  Could be readily modified to
        identify wider stripes if needed.

        :param dataset: input dataset (ECOSTRESS scene)
        :param data_quality: data quality mask
        :param threshold: threshold for identifying stripes (defined as multiple of MAD)

        :return: updated data quality mask

        """
        return _find_horizontal_stripes(dataset, data_quality, self.n_bands, threshold)

    def _build_model(self, index: int) -> tf.keras.Model:
        """Build an autoencoder model that predicts both mean and variance. Based on arXiv:1612.01474
        :param index: Index of the model in the ensemble
        :return: Keras model
        """
        # Import locally, so we don't depend on this unless we use it
        import tensorflow as tf  # type: ignore
        from tensorflow.keras import layers, Model  # type: ignore
        from tensorflow.keras.optimizers import Adam  # type: ignore

        tf.random.set_seed(self.seed + index)
        np.random.seed(self.seed + index)

        inputs = layers.Input(shape=(self.grid_size, self.grid_size, self.n_bands))

        # Mask missing data (0 for missing, 1 for valid)
        mask = layers.Lambda(
            lambda x: tf.cast(~tf.math.is_nan(x), tf.float32), output_shape=lambda s: s
        )(inputs)

        def my_nan_to_num(x):  # type: ignore
            return tf.cond(
                tf.equal(tf.size(x), 0),
                lambda: x,
                lambda: tf.where(tf.math.is_nan(x), tf.zeros_like(x), x),
            )

        masked_inputs = layers.Lambda(my_nan_to_num, output_shape=lambda s: s)(inputs)

        masked_inputs = layers.Concatenate(axis=-1)([masked_inputs, mask])

        # Encoder
        x = layers.Flatten()(masked_inputs)
        for units in self.encoder_layers:
            x = layers.Dense(units, activation=self.activation)(x)

        # Latent space
        latent = layers.Dense(self.latent_dim, activation=self.activation)(x)

        # Decoder
        x = latent
        for units in self.decoder_layers:
            x = layers.Dense(units, activation=self.activation)(x)

        # Output layers (predict mean and log-variance)
        mean_outputs = layers.Dense(
            self.grid_size * self.grid_size * self.n_bands, activation="linear"
        )(x)
        var_outputs = layers.Dense(
            self.grid_size * self.grid_size * self.n_bands, activation="softplus"
        )(x)  # Ensure positive variance

        mean_outputs = layers.Reshape((self.grid_size, self.grid_size, self.n_bands))(
            mean_outputs
        )
        var_outputs = layers.Reshape((self.grid_size, self.grid_size, self.n_bands))(
            var_outputs
        )

        # need to merge outputs to use custom loss function.
        merged_output = layers.Concatenate(axis=-1)([mean_outputs, var_outputs])
        model = Model(inputs, merged_output)
        model.compile(optimizer=Adam(learning_rate=0.005), loss=self.nll_loss)

        return model

    def model_predict(self, data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """predict mean and uncertainty given input data from the ensemble of models
        :param data: input data
        :return: mean_preds, total_uncertainty (1 sigma)
        """

        # Get predictions from each ensemble model
        ensemble_means = []
        ensemble_vars = []
        for model in self.models:
            merged_output = model.predict(data, verbose=0)
            mean_preds = merged_output[..., : self.n_bands]
            var_preds = merged_output[..., self.n_bands :]
            ensemble_means.append(mean_preds)
            ensemble_vars.append(var_preds)

        ensemble_means2 = np.stack(ensemble_means, axis=0)
        ensemble_vars2 = np.stack(ensemble_vars, axis=0)

        # Mean and var across the ensemble dimension
        mean_preds = np.mean(ensemble_means2, axis=0)
        aleatoric_uncertainty = np.mean(ensemble_vars2, axis=0)
        epistemic_uncertainty = np.var(ensemble_means2, axis=0, ddof=1)
        total_uncertainty = aleatoric_uncertainty + epistemic_uncertainty
        # convert uncertainty from var to std
        total_uncertainty = np.sqrt(total_uncertainty)

        return mean_preds, total_uncertainty

    def nll_loss(self, y_true: tf.Tensor, outputs: tf.Tensor) -> tf.Tensor:
        """Negative log likelihood loss function for probabilistic regression.
        Loss is offset by 5 and has no direct physical meaning.
        The last n_bands channels in y_true contain the mask.
        :param y_true: [True values, mask]
        :param outputs: Predictions
        :return: Loss
        """
        # Import locally, so we don't depend on this unless we use it
        import tensorflow as tf  # type: ignore

        # y_true shape: (batch, grid_size, grid_size, n_bands + n_bands_for_mask)

        y_true_data = y_true[..., : self.n_bands]  # the real 'targets'

        # The last n_bands channels in y_true contain the mask.
        missing_data_mask = (
            1 - y_true[..., self.n_bands :]
        )  # shape: (batch, gs, gs, n_bands)

        # outputs was merged: [mean_outputs, log_var_outputs]
        y_pred = outputs[..., : self.n_bands]
        log_var = outputs[..., self.n_bands :]

        nll = (
            0.5 * (tf.math.log(log_var) + tf.square(y_true_data - y_pred) / log_var) + 5
        )

        # Multiply by mask so that only pixels flagged as "to fill" remain in cost.
        nll = nll * missing_data_mask

        # Average across all relevant pixels where mask is 1.
        loss = tf.reduce_sum(nll) / tf.reduce_sum(missing_data_mask)

        return loss

    def normalize_data(self, datain: np.ndarray) -> np.ndarray:
        """
        Normalize the input data by converting to z-scores and handling fill values.
        """
        dat = datain.copy()

        if self.mu is None or self.sigma is None:
            self.mu = np.zeros(dat.shape[2])
            self.sigma = np.zeros(dat.shape[2])
            for i in range(dat.shape[2]):
                self.mu[i] = np.nanmean(dat[:, :, i])
                self.sigma[i] = np.nanstd(dat[:, :, i])

        for i in range(dat.shape[2]):
            dat[:, :, i] = (dat[:, :, i] - self.mu[i]) / self.sigma[i]
        return dat

    def denormalize_data(
        self, normalized_data: np.ndarray, std_only: bool = False
    ) -> np.ndarray:
        """
        Convert normalized data back to original scale.
        """
        if self.mu is None or self.sigma is None:
            raise ValueError("Must run normalize_data before denormalize_data")

        result = normalized_data.copy()
        if std_only:
            for i in range(result.shape[2]):
                result[:, :, i] = result[:, :, i] * self.sigma[i]
        else:
            for i in range(result.shape[2]):
                result[:, :, i] = result[:, :, i] * self.sigma[i] + self.mu[i]

        return result

    def create_training_samples(
        self, dataset: np.ndarray, missing_mask: np.ndarray, n_samples: int = 10000
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Create training samples from the normalized dataset.

        Args:
            dataset: Normalized dataset
            missing_mask: Mask indicating missing values
            n_samples: Number of samples to create
        Returns:
            training_x: Input samples with missing values
            training_y: Target samples with complete data and mask concatenated
        """
        logger.info("Creating training samples...")

        h, w, _ = dataset.shape
        training_x: list[np.ndarray] = []
        training_y: list[np.ndarray] = []
        sampled = set()

        if n_samples > h * w // 2:
            raise ValueError(
                "Number of requested samples is too large. Please reduce the number of samples."
            )

        loop_count = 0
        while len(training_x) < n_samples:
            loop_count += 1
            if loop_count > 100 * n_samples:
                raise ValueError(
                    "Could not find enough training samples. Please check the data."
                )

            i = np.random.randint(self.grid_size // 2, h - self.grid_size // 2)
            j = np.random.randint(self.grid_size // 2, w - self.grid_size // 2)

            grid_slice = slice(i - self.grid_size // 2, i + self.grid_size // 2 + 1)
            col_slice = slice(j - self.grid_size // 2, j + self.grid_size // 2 + 1)

            grid = dataset[grid_slice, col_slice, :]

            if np.any(missing_mask[grid_slice, col_slice, :] > 0):
                continue

            if (i, j) in sampled:
                continue
            sampled.add((i, j))

            masked_grid = grid.copy()

            if self.n_bands == 5:
                # Randomly mask 50% of bands. 1 means keep, 0 means remove
                mask = np.random.random(self.n_bands) < 0.5
            elif self.n_bands == 3:
                # randomly choose one of the 3 bands to mask
                band_to_mask = np.random.randint(0, 3)
                mask = np.ones(3, dtype=bool)
                mask[band_to_mask] = False
            else:
                raise ValueError("n_bands must be 3 or 5")

            masked_grid[:, :, ~mask] = np.nan

            # if we don't have enough good data, or did not mask any -> skip this sample
            if (np.sum(mask) < self.n_good_bands_required) or (
                np.sum(mask) == self.n_bands
            ):
                continue

            mask_expanded = np.tile(mask, (self.grid_size, self.grid_size, 1)).astype(
                np.float32
            )
            grid = np.concatenate([grid, mask_expanded], axis=-1)

            training_x.append(masked_grid)
            training_y.append(grid)

        logger.info(
            f"Created {len(training_x)} training samples out of {loop_count} attempts."
        )
        return np.array(training_x), np.array(training_y)

    def train(
        self,
        dataset: np.ndarray,
        missing_mask: np.ndarray,
        epochs: int = 10,
        batch_size: int = 32,
        n_samples: int = 10000,
        validate: bool = False,
        validate_threshold: float = 5,
    ) -> None:
        """Train the ensemble models with Negative Log Likelihood loss.

        Args:
            dataset: The input dataset with missing values.
            missing_mask: Mask indicating missing values.
            epochs: Number of training epochs.
            batch_size: Size of the training batches.
            n_samples: Number of samples to create for training.
            validate: Boolean indicating whether to validate the model after training.
            validate_threshold: RMSE threshold for validation

        """
        # Import locally, so we don't depend on this unless we use it
        from sklearn.model_selection import train_test_split  # type: ignore

        # subset data to n_bands
        if self.n_bands == 3:
            dataset_subset = dataset[:, :, [1, 3, 4]].copy()
            missing_mask_subset = missing_mask[:, :, [1, 3, 4]]
        elif self.n_bands == 5:
            dataset_subset = dataset.copy()
            missing_mask_subset = missing_mask
        else:
            raise ValueError("n_bands must be 3 or 5")

        # set missing data to nan. Required by interpolation model to work correctly
        dataset_subset[missing_mask_subset != 0] = np.nan

        normalized_data = self.normalize_data(dataset_subset)
        training_x, training_y = self.create_training_samples(
            normalized_data, missing_mask_subset, n_samples=n_samples
        )

        train_x, test_x, train_y, test_y = train_test_split(
            training_x, training_y, test_size=0.1, random_state=self.seed
        )

        for idx, model in enumerate(self.models):
            logger.info(f"\nTraining model {idx + 1} / {self.n_ensemble}")

            train_x_subset, _, train_y_subset, _ = train_test_split(
                train_x, train_y, test_size=0.5, random_state=self.seed + idx
            )

            model.fit(
                train_x_subset,
                train_y_subset,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(test_x, test_y),
                shuffle=True,
                verbose=1 if self.verbose else 0,
            )

        # test model to calculate MSE and expected calibration error
        if validate:
            self.test(
                test_x,
                test_y[:, :, :, : self.n_bands],
                rmse_threshold=validate_threshold,
            )

    def test(
        self, test_x: np.ndarray, test_y: np.ndarray, rmse_threshold: float = 5
    ) -> None:
        """
        Test the ensemble models on the test set.

        Args:
            test_x: Input test data (already normalized)
            test_y: Target test data (already normalized)

        """
        # Calculate MSE of model mean
        mean_preds, _ = self.model_predict(test_x)

        # denormalize the data
        predictions = self.denormalize_data(mean_preds)
        test_y = self.denormalize_data(test_y)

        interpolated_mask = np.isnan(test_x[:, :, :, : self.n_bands])

        # set all other predictions to nan
        predictions[~interpolated_mask] = np.nan

        # Calculate RMSE for each band
        rmses = []
        for band in range(self.n_bands):
            mse = np.nanmean((predictions[:, :, :, band] - test_y[:, :, :, band]) ** 2)
            rmses.append(np.sqrt(mse))
        logger.info(f"RMSE for bands: {[f'{rmse:.3f}' for rmse in rmses]} W/m^2/sr/um")

        # throw exception if RMSE is too high
        # TODO: how would we want to log this as a warning?
        if np.any(np.array(rmses) > rmse_threshold):
            raise ValueError(
                f"RMSE of Interpolation is higher than {rmse_threshold} W/m^2/sr/um. "
            )

    def interpolate_missing(
        self, dataset: np.ndarray, data_quality: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Interpolate missing values using the ensemble of models.
        Provides uncertainties.
        For 3-band data sets, only bands 2, 4, and 5 are processed.

        Args:
            dataset: Input dataset with missing values with 5 bands
            data_quality: Data quality mask indicating missing values
        Returns:
            denorm_result_combined: Interpolated dataset with missing values filled
            denorm_uncertainty_combined: Uncertainty map for the interpolated values
            data_quality_combined: Updated data quality mask
        """

        # subset data to n_bands
        if self.n_bands == 3:
            bands_to_process = [1, 3, 4]
            dataset_subset_original = dataset[:, :, bands_to_process]
            dataset_subset = dataset_subset_original.copy()
            data_quality_subset = data_quality[:, :, bands_to_process]
        elif self.n_bands == 5:
            dataset_subset_original = dataset
            dataset_subset = dataset_subset_original.copy()
            data_quality_subset = data_quality
        else:
            raise ValueError("n_bands must be 3 or 5")

        # set missing data to nan. Required by interpolation model to work correctly
        dataset_subset[data_quality_subset != 0] = np.nan

        normalized_data = self.normalize_data(dataset_subset)
        uncertainty_map = np.zeros_like(dataset_subset)

        half = self.grid_size // 2
        # missing mask - note we should *not* fill in pixels that are
        # missing because they are not actually seen. This data really
        # isn't there, and we shouldn't interpolate to try filling it
        # in.
        missing_boolean_mask = (data_quality_subset != DQI_GOOD) & (
            data_quality_subset != DQI_NOT_SEEN
        )

        interpolation_candidates = missing_boolean_mask

        missing_any_band = np.any(interpolation_candidates, axis=2)

        if self.grid_size > 1:
            missing_any_band[:half, :] = False
            missing_any_band[-half:, :] = False
            missing_any_band[:, :half] = False
            missing_any_band[:, -half:] = False

        missing_indices = np.argwhere(missing_any_band)
        missing_coords = [tuple(idx) for idx in missing_indices]

        if len(missing_coords) == 0:
            logger.info(
                "No missing data found, returning original dataset without interpolating."
            )
            return (dataset, np.zeros_like(dataset), data_quality)

        all_subgrids = np.zeros(
            (len(missing_coords), self.grid_size, self.grid_size, self.n_bands),
            dtype=np.float32,
        )
        for idx, (i, j) in enumerate(missing_coords):
            all_subgrids[idx] = normalized_data[
                i - half : i + half + 1, j - half : j + half + 1, :
            ]

        mean_preds, uncertainty = self.model_predict(all_subgrids)

        result = np.zeros_like(dataset_subset)
        # Write predictions back into 'result' and 'uncertainty_map'
        for idx, (i, j) in enumerate(missing_coords):
            for band in range(self.n_bands):
                if interpolation_candidates[i, j, band]:
                    # check that we have a valid prediciton here. Requires at least self.n_good_bands_required good bands
                    if (
                        np.sum(data_quality_subset[i, j, :] == DQI_GOOD)
                        >= self.n_good_bands_required
                    ):
                        result[i, j, band] = mean_preds[idx, half, half, band]
                        uncertainty_map[i, j, band] = uncertainty[idx, half, half, band]
                        data_quality_subset[i, j, band] = DQI_INTERPOLATED

        # Convert back to original scale
        denorm_result = self.denormalize_data(result)
        denorm_uncertainty = self.denormalize_data(uncertainty_map, std_only=True)

        # OPTIONAL: remove stripes we identified from data_quality
        # that we were not able to interpolate, but were originally
        # marked as good. In find_horizontal_stripes we updated
        # data_quality, but not dataset so we can use this to identify
        # DQI_STRIPE_NOT_INTERPOLATED that were not there originally.
        data_quality_subset[
            (data_quality_subset == DQI_STRIPE_NOT_INTERPOLATED)
            & (dataset_subset_original > self.fill_value_threshold)
        ] = DQI_GOOD
        # add missing data back to the result if n_bands == 3
        if self.n_bands == 3:
            denorm_uncertainty_combined = np.zeros_like(dataset)
            denorm_uncertainty_combined[:, :, bands_to_process] = denorm_uncertainty

            data_quality_combined = data_quality.copy()
            data_quality_combined[:, :, bands_to_process] = data_quality_subset

            denorm_result_combined = dataset.copy()
            denorm_result_combined[:, :, bands_to_process] = denorm_result
            # replace denorm_result_combined in bands_to_process with dataset where data_quality_subset is not DQI_INTERPOLATED
            # ensures that if there was a value that we wanted to interpolate but could not, we keep the original value
            denorm_result_combined[~(data_quality_combined == DQI_INTERPOLATED)] = (
                dataset[~(data_quality_combined == DQI_INTERPOLATED)]
            )

        elif self.n_bands == 5:
            # replace denorm_result_combined in bands_to_process with dataset where data_quality_subset is not DQI_INTERPOLATED
            # ensures that if there was a value that we wanted to interpolate but could not, we keep the original value
            denorm_result[~(data_quality_subset == DQI_INTERPOLATED)] = dataset[
                ~(data_quality_subset == DQI_INTERPOLATED)
            ]

            denorm_result_combined = denorm_result
            denorm_uncertainty_combined = denorm_uncertainty
            data_quality_combined = data_quality_subset

        # TODO: I added one additional return value, the interpolated_data. This will break things downstream.
        return (
            denorm_result_combined,
            denorm_uncertainty_combined,
            data_quality_combined,
        )


class EcostressLocalWindowKNNInterpolator(object):
    """Local sliding-window KNN interpolator.
    - For each pixel needing interpolation (excluding NOT_SEEN), use an N x N window centered on the pixel
    - Build a KNN regressor from neighboring pixels inside the window where the target band is GOOD and
      the selected feature bands are GOOD
    - Features are the radiances from other bands at the same pixel location
    - Prediction uses the feature vector at the center pixel; uncertainty is residual std on training set

    Notes:
    - Works on 5-band data by default; for 3-band processing uses bands [2, 4, 5] -> indices [1, 3, 4]
    """

    def __init__(
        self,
        n_bands: int = 5,
        window_size: int = 201,  # must be odd
        n_neighbors: int = 10,
        max_train_samples: int = 5000,
        min_feature_bands_for_prediction: int = 2,
        max_feature_bands_for_prediction: int = 3,
        feature_selection_scope: str = "center",  # "center" or "window_best"
        random_state: int = 1234,
        min_train_per_window: int = 15,  # skip prediction if fewer usable train pixels in window
        block_step: int | None = None,  # default: window_size // 2
        inner_size: int | None = None,  # default: block_step
        knn_n_jobs: int = 1,
        exclude_full_bad_edge_columns: bool = True,  # columns that are fully bad in any band, typically on the edges of a scene
        allow_relaxed_center_drop: bool = True,  # avoids missing blocks due to sporadic missing data in center pixels
        center_drop_max_fraction: float = 0.10,  # maximum fraction of centers that can be dropped
    ) -> None:
        if window_size < 3 or window_size % 2 == 0:
            raise ValueError("window_size must be an odd integer >= 3")
        if n_neighbors < 1:
            raise ValueError("n_neighbors must be >= 1")

        self.n_bands = n_bands
        self.window_size = window_size
        self.n_neighbors = n_neighbors
        self.max_train_samples = max_train_samples
        self.min_feature_bands_for_prediction = min_feature_bands_for_prediction
        self.max_feature_bands_for_prediction = max_feature_bands_for_prediction
        self.feature_selection_scope = feature_selection_scope
        self.random_state = random_state
        self.min_train_per_window = max(0, min_train_per_window)
        self.block_step = (
            block_step if block_step is not None else max(1, window_size // 2)
        )
        self.inner_size = inner_size if inner_size is not None else self.block_step
        self.knn_n_jobs = knn_n_jobs
        self.exclude_full_bad_edge_columns = exclude_full_bad_edge_columns
        self.allow_relaxed_center_drop = allow_relaxed_center_drop
        self.center_drop_max_fraction = max(0.0, min(0.5, center_drop_max_fraction))

    def _bands_to_process(self) -> list[int]:
        if self.n_bands == 3:
            return [1, 3, 4]
        elif self.n_bands == 5:
            return [0, 1, 2, 3, 4]
        else:
            raise ValueError("n_bands must be 3 or 5")

    def _feature_bands(self, target_band: int) -> list[int]:
        return [b for b in self._bands_to_process() if b != target_band]

    def _select_features_for_center(
        self,
        dataset: np.ndarray,
        data_quality: np.ndarray,
        target_band: int,
        i: int,
        j: int,
        window_slice_rows: slice,
        window_slice_cols: slice,
    ) -> list[int]:
        """Choose feature bands to use for this prediction.
        - If scope == 'center': use other bands that are GOOD at the center pixel
        - If scope == 'window_best': rank other bands by fraction of GOOD pixels in the window and
          take up to max_feature_bands_for_prediction, while requiring they are GOOD at center too
        """
        candidates = self._feature_bands(target_band)

        # Bands that are GOOD at the center pixel
        good_at_center = [b for b in candidates if data_quality[i, j, b] == DQI_GOOD]
        if self.feature_selection_scope == "center":
            selected = good_at_center[: self.max_feature_bands_for_prediction]
            return (
                selected
                if len(selected) >= self.min_feature_bands_for_prediction
                else []
            )

        # window_best: rank by good fraction inside window, but must be good at center
        hmask = data_quality[window_slice_rows, window_slice_cols, :]
        fractions: list[tuple[int, float]] = []
        for b in candidates:
            fr = float(np.mean(hmask[:, :, b] == DQI_GOOD))
            fractions.append((b, fr))
        eligible_sorted = sorted(
            [b for (b, fr) in fractions if b in good_at_center],
            key=lambda bb: next(fr for (bbb, fr) in fractions if bbb == bb),
            reverse=True,
        )
        selected = eligible_sorted[: self.max_feature_bands_for_prediction]
        return (
            selected if len(selected) >= self.min_feature_bands_for_prediction else []
        )

    def _fit_knn_and_predict(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_pred: np.ndarray,
        batch: bool = False,
    ) -> tuple[np.ndarray, np.ndarray | float]:
        from sklearn.neighbors import KNeighborsRegressor  # type: ignore

        if X_train.shape[0] == 0:
            return np.array([]), np.nan

        # Optionally subsample to cap training size for speed
        if X_train.shape[0] > self.max_train_samples:
            rng = np.random.default_rng(self.random_state)
            idx = rng.choice(X_train.shape[0], self.max_train_samples, replace=False)
            X_train = X_train[idx]
            y_train = y_train[idx]

        model = KNeighborsRegressor(
            n_neighbors=self.n_neighbors,
            weights="distance",
            algorithm="kd_tree",
            n_jobs=self.knn_n_jobs,
        )
        model.fit(X_train, y_train)
        # Predictions (initial, used as fallback) and predictive-variance-based UQ
        if batch:
            y_pred = model.predict(X_pred)
        else:
            y_pred = model.predict(X_pred.reshape(1, -1))

        # Per-prediction uncertainty via predictive variance using neighbor weights
        n_nbrs = min(self.n_neighbors, max(1, X_train.shape[0]))
        eps = 1e-6
        if batch:
            dists, idxs = model.kneighbors(
                X_pred, n_neighbors=n_nbrs, return_distance=True
            )
            uq_vals = np.zeros(dists.shape[0], dtype=float)
            y_pred_vals = np.array(y_pred, dtype=float)
            for r in range(dists.shape[0]):
                d = dists[r]
                ii = idxs[r]
                y_nei = y_train[ii].astype(float)
                if y_nei.size == 0:
                    # keep fallback prediction and zero UQ
                    uq_vals[r] = 0.0
                    continue
                # Drop exact self-match if present to avoid zero-variance edge case
                if d[0] <= eps and len(d) >= 2:
                    d = d[1:]
                    y_nei = y_nei[1:]
                w = 1.0 / (d + eps)
                ws = float(np.sum(w))
                if ws <= 0:
                    uq_vals[r] = 0.0
                    continue
                w = w / ws
                mu = float(np.dot(w, y_nei))
                y_pred_vals[r] = mu
                w2_sum = float(np.sum(w**2))
                denom = max(1e-12, 1.0 - w2_sum)
                sw2 = float(np.sum(w * (y_nei - mu) ** 2)) / denom
                # Predictive variance combines aleatoric (sw2) and epistemic (sw2 * w2_sum)
                var_pred = sw2 * (1.0 + w2_sum)
                uq_vals[r] = float(np.sqrt(max(0.0, var_pred)))
            return y_pred_vals, uq_vals
        else:
            dists, idxs = model.kneighbors(
                X_pred.reshape(1, -1), n_neighbors=n_nbrs, return_distance=True
            )
            d = dists[0]
            ii = idxs[0]
            y_nei = y_train[ii].astype(float)
            if y_nei.size == 0:
                return y_pred, 0.0
            # Drop exact self-match if present (only when we have at least 2 neighbors)
            if d[0] <= eps and len(d) >= 2:
                d = d[1:]
                y_nei = y_nei[1:]
            w = 1.0 / (d + eps)
            ws = float(np.sum(w))
            if ws <= 0:
                return y_pred, 0.0
            w = w / ws
            mu = float(np.dot(w, y_nei))
            y_pred = np.array([mu], dtype=float)
            w2_sum = float(np.sum(w**2))
            denom = max(1e-12, 1.0 - w2_sum)
            sw2 = float(np.sum(w * (y_nei - mu) ** 2)) / denom
            # Predictive variance combines aleatoric (sw2) and epistemic (sw2 * w2_sum)
            var_pred = sw2 * (1.0 + w2_sum)
            uq_val = float(np.sqrt(max(0.0, var_pred)))
            return y_pred, uq_val

    def interpolate_missing(
        self, dataset: np.ndarray, data_quality: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Interpolate missing pixels using an N x N sliding window KNN per pixel.
        Returns (interpolated_dataset, uncertainty, updated_data_quality).
        """
        result = dataset.copy()
        uncertainty = np.zeros_like(dataset)
        dq_out = data_quality.copy()

        h, w, _ = dataset.shape

        bands = self._bands_to_process()
        # Pre-compute per-band edge columns that are fully "needs interpolation" and should be excluded
        excluded_cols_per_band: dict[int, tuple[int, int]] = {}
        # Also compute a global edge exclusion based on any band being fully-bad in a column
        excluded_cols_mask_global = np.zeros(w, dtype=bool)
        if self.exclude_full_bad_edge_columns:
            for band in bands:
                needs_band = (dq_out[:, :, band] != DQI_GOOD) & (
                    dq_out[:, :, band] != DQI_NOT_SEEN
                )
                col_all = np.all(needs_band, axis=0)
                # count consecutive from left
                left_count = 0
                while left_count < w and col_all[left_count]:
                    left_count += 1
                # count consecutive from right
                right_count = 0
                while right_count < (w - left_count) and col_all[w - 1 - right_count]:
                    right_count += 1
                excluded_cols_per_band[band] = (left_count, right_count)
            # Global mask: columns fully-bad in any band, but only contiguous from edges
            if len(bands) > 0:
                # Build OR across bands for fully-bad columns
                col_all_stack = []
                for band in bands:
                    needs_band = (dq_out[:, :, band] != DQI_GOOD) & (
                        dq_out[:, :, band] != DQI_NOT_SEEN
                    )
                    col_all_stack.append(np.all(needs_band, axis=0))
                global_full_bad = np.any(np.stack(col_all_stack, axis=0), axis=0)
                # Left contiguous run
                left_g = 0
                while left_g < w and global_full_bad[left_g]:
                    left_g += 1
                # Right contiguous run
                right_g = 0
                while right_g < (w - left_g) and global_full_bad[w - 1 - right_g]:
                    right_g += 1
                if left_g > 0:
                    excluded_cols_mask_global[:left_g] = True
                if right_g > 0:
                    excluded_cols_mask_global[w - right_g :] = True

        for band in bands:
            needs = (dq_out[:, :, band] != DQI_GOOD) & (
                dq_out[:, :, band] != DQI_NOT_SEEN
            )
            # Exclude fully-bad edge columns for this band
            if self.exclude_full_bad_edge_columns:
                left_c, right_c = excluded_cols_per_band.get(band, (0, 0))
                if left_c > 0:
                    needs[:, :left_c] = False
                if right_c > 0:
                    needs[:, w - right_c :] = False
                # Also exclude globally flagged edge columns (fully-bad in any band)
                if np.any(excluded_cols_mask_global):
                    needs[:, excluded_cols_mask_global] = False
            if not np.any(needs):
                continue

            # Block processing mode: slide window with stride and predict inner region in batch
            step = self.block_step
            inner = self.inner_size
            margin = max(0, (self.window_size - inner) // 2)
            win_h = self.window_size
            win_w = self.window_size

            # enumerate window top-left indices
            row_starts = list(range(0, max(1, h - win_h + 1), step))
            col_starts = list(range(0, max(1, w - win_w + 1), step))
            # Edge handling: ensure we include a final block aligned to the bottom/right edges
            # even if the step does not land exactly on the last possible start.
            if h - win_h >= 0:
                last_r0 = h - win_h
                if len(row_starts) == 0 or row_starts[-1] != last_r0:
                    row_starts.append(last_r0)
            if w - win_w >= 0:
                last_c0 = w - win_w
                if len(col_starts) == 0 or col_starts[-1] != last_c0:
                    col_starts.append(last_c0)
            total_blocks = len(row_starts) * len(col_starts)
            try:
                from tqdm import tqdm  # type: ignore

                block_iter = tqdm(
                    ((r0, c0) for r0 in row_starts for c0 in col_starts),
                    total=total_blocks,
                    desc=f"KNN_WINDOW blocks band {band + 1}",
                )
            except Exception:
                block_iter = ((r0, c0) for r0 in row_starts for c0 in col_starts)

            for r0, c0 in block_iter:
                r1 = min(h, r0 + win_h)
                c1 = min(w, c0 + win_w)
                if r1 - r0 < 3 or c1 - c0 < 3:
                    continue
                rs = slice(r0, r1)
                cs = slice(c0, c1)

                # center of window
                ir0 = r0 + margin
                ir1 = min(r1, ir0 + inner)
                ic0 = c0 + margin
                ic1 = min(c1, ic0 + inner)
                # Edge handling: expand inner region to touch image borders when the window touches borders.
                # This ensures border pixels can be predicted when possible.
                if r0 == 0:
                    ir0 = r0
                if r1 == h:
                    ir1 = r1
                if c0 == 0:
                    ic0 = c0
                if c1 == w:
                    ic1 = c1
                if ir0 >= ir1 or ic0 >= ic1:
                    continue

                # Candidate centers needing interpolation in inner region
                needs_inner = needs[ir0:ir1, ic0:ic1]
                # Additional edge handling: if this block touches left or right edge, exclude inner columns
                # that are fully-bad across rows in ANY band within this window. This prevents edge columns
                # that are missing in other channels from constraining shared feature selection.
                touches_left_edge = ic0 == 0
                touches_right_edge = ic1 == w
                if self.exclude_full_bad_edge_columns and (
                    touches_left_edge or touches_right_edge
                ):
                    # For columns inside current window [c0:c1), compute if they are fully-bad across rows for any band
                    # within the window rows [r0:r1).
                    col_fully_bad_any_band = np.zeros(c1 - c0, dtype=bool)
                    for btmp in bands:
                        needs_b_win = (dq_out[rs, cs, btmp] != DQI_GOOD) & (
                            dq_out[rs, cs, btmp] != DQI_NOT_SEEN
                        )
                        col_fully_bad_any_band |= np.all(needs_b_win, axis=0)
                    # Map to inner slice [ic0:ic1)
                    inner_start = ic0 - c0
                    inner_end = inner_start + (ic1 - ic0)
                    inner_col_mask = col_fully_bad_any_band[inner_start:inner_end]
                    if np.any(inner_col_mask):
                        needs_inner[:, inner_col_mask] = False
                if not np.any(needs_inner):
                    continue
                inner_coords = np.argwhere(needs_inner)
                if inner_coords.size == 0:
                    continue

                # Feature selection and relaxed center drop:
                # Try strict shared-features across all centers first. If that fails and allowed,
                # relax by dropping up to center_drop_max_fraction of centers lacking selected features.
                centers_abs = [(ir0 + di, ic0 + dj) for di, dj in inner_coords]
                all_features = self._feature_bands(band)

                def rank_features_by_window_good(fr_candidates: list[int]) -> list[int]:
                    if self.feature_selection_scope == "window_best":
                        hmask_local = dq_out[rs, cs, :]
                        fr_list: list[tuple[int, float]] = []
                        for fb_ in fr_candidates:
                            fr_val = float(np.mean(hmask_local[:, :, fb_] == DQI_GOOD))
                            fr_list.append((fb_, fr_val))
                        return [
                            fb_
                            for fb_, _ in sorted(
                                fr_list, key=lambda t: t[1], reverse=True
                            )
                        ]
                    # default: keep original order
                    return list(fr_candidates)

                # Strict: require every center has the feature
                strict_feats = [
                    fb
                    for fb in all_features
                    if all(dq_out[i, j, fb] == DQI_GOOD for (i, j) in centers_abs)
                ]
                strict_feats = rank_features_by_window_good(strict_feats)[
                    : self.max_feature_bands_for_prediction
                ]

                selected_feats: list[int] = []
                centers_keep_mask: np.ndarray | None = None

                if len(strict_feats) >= self.min_feature_bands_for_prediction:
                    selected_feats = strict_feats
                    # all centers kept in strict case
                    centers_keep_mask = np.ones(len(centers_abs), dtype=bool)
                elif self.allow_relaxed_center_drop:
                    # Relaxed: choose features that are good at the center for most centers
                    # Compute availability matrix [num_centers x num_candidate_features]
                    num_centers = len(centers_abs)
                    if num_centers == 0:
                        continue
                    # Rank all features by good fraction at centers
                    fr_per_feat: list[tuple[int, float]] = []
                    for fb in all_features:
                        good_count = sum(
                            1 for (i, j) in centers_abs if dq_out[i, j, fb] == DQI_GOOD
                        )
                        fr_per_feat.append((fb, good_count / float(num_centers)))
                    ranked_feats = [
                        fb
                        for fb, _ in sorted(
                            fr_per_feat, key=lambda t: t[1], reverse=True
                        )
                    ]
                    # Try to pick up to max_feature_bands while ensuring center retention >= 1 - drop_frac
                    for take_k in range(
                        self.max_feature_bands_for_prediction,
                        self.min_feature_bands_for_prediction - 1,
                        -1,
                    ):
                        cand = ranked_feats[:take_k]
                        if len(cand) < self.min_feature_bands_for_prediction:
                            continue
                        # Compute which centers have all selected features
                        keep = np.array(
                            [
                                all(dq_out[i, j, fb] == DQI_GOOD for fb in cand)
                                for (i, j) in centers_abs
                            ],
                            dtype=bool,
                        )
                        keep_count = int(np.count_nonzero(keep))
                        if keep_count > 0 and (keep_count / float(num_centers)) >= (
                            1.0 - self.center_drop_max_fraction
                        ):
                            selected_feats = cand
                            centers_keep_mask = keep
                            break
                    # If still nothing, try any minimal combo that yields at least min centers
                    if len(selected_feats) == 0:
                        for take_k in range(
                            self.min_feature_bands_for_prediction,
                            self.max_feature_bands_for_prediction + 1,
                        ):
                            cand = ranked_feats[:take_k]
                            if len(cand) < self.min_feature_bands_for_prediction:
                                continue
                            keep = np.array(
                                [
                                    all(dq_out[i, j, fb] == DQI_GOOD for fb in cand)
                                    for (i, j) in centers_abs
                                ],
                                dtype=bool,
                            )
                            keep_count = int(np.count_nonzero(keep))
                            if keep_count > 0:
                                selected_feats = cand
                                centers_keep_mask = keep
                                break
                # If selection still insufficient, skip block
                if (
                    len(selected_feats) < self.min_feature_bands_for_prediction
                    or centers_keep_mask is None
                    or not np.any(centers_keep_mask)
                ):
                    continue

                # Optionally cap selected features by window quality again
                selected_feats = rank_features_by_window_good(selected_feats)[
                    : self.max_feature_bands_for_prediction
                ]

                # Build training set for window
                good_target = dq_out[rs, cs, band] == DQI_GOOD
                mask = good_target.copy()
                for fb in selected_feats:
                    mask &= dq_out[rs, cs, fb] == DQI_GOOD
                if not np.any(mask):
                    continue
                train_count = int(np.count_nonzero(mask))
                if train_count < max(self.n_neighbors, self.min_train_per_window):
                    continue
                X_list: list[np.ndarray] = []
                for fb in selected_feats:
                    X_list.append(dataset[rs, cs, fb][mask])
                X_train = np.stack(X_list, axis=1)
                y_train = dataset[rs, cs, band][mask]

                # Build batch prediction matrix for centers that have all selected features
                centers_abs_keep = [
                    centers_abs[idx] for idx, k in enumerate(centers_keep_mask) if k
                ]
                if len(centers_abs_keep) == 0:
                    continue
                X_pred = np.stack(
                    [
                        np.array(
                            [dataset[i, j, fb] for fb in selected_feats], dtype=float
                        )
                        for (i, j) in centers_abs_keep
                    ],
                    axis=0,
                )

                # Predict in batch
                y_pred, uq = self._fit_knn_and_predict(
                    X_train, y_train, X_pred, batch=True
                )
                if y_pred.size == 0:
                    continue
                # Write back
                for idx, (i, j) in enumerate(centers_abs_keep):
                    result[i, j, band] = float(y_pred[idx])
                    if isinstance(uq, np.ndarray):
                        uncertainty[i, j, band] = float(uq[idx])
                    else:
                        uncertainty[i, j, band] = float(uq)
                    dq_out[i, j, band] = DQI_INTERPOLATED

        # Revert any remaining stripe flags to GOOD if original data was valid
        dq_out[
            (dq_out == DQI_STRIPE_NOT_INTERPOLATED) & (dataset > fill_value_threshold)
        ] = DQI_GOOD

        return result, uncertainty, dq_out


__all__ = ["EcostressAeDeepEnsembleInterpolate", "EcostressLocalWindowKNNInterpolator"]
