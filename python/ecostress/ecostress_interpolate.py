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
        self.verbose = verbose

        # Will store normalization parameters
        self.mu: np.ndarray | None = None
        self.sigma: np.ndarray | None = None

        # Each member of the ensemble is a separate model
        self.models = [self._build_model(i) for i in range(n_ensemble)]

    def find_horizontal_stripes(
        self, dataset: np.ndarray, data_quality: np.ndarray, threshold: int = 5
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

        if self.n_bands == 3:
            bands_to_process = [1, 3, 4]
        elif self.n_bands == 5:
            bands_to_process = [0, 1, 2, 3, 4]
        else:
            raise ValueError("n_bands must be 3 or 5")

        # make a copy of the dataset so we do not modify the original
        dataset = dataset.copy()

        # remove bad
        dataset[dataset < self.fill_value_threshold] = np.nan

        for band in bands_to_process:
            band_data = dataset[:, :, band]

            # Compute row-wise differences to detect rapid intensity changes
            row_diff = np.abs(np.diff(band_data, axis=0))
            row_diff = np.concatenate(
                [np.zeros((1, row_diff.shape[1])), row_diff], axis=0
            )

            # First summarize the pixel-wise differences for each row using the mean
            row_diff_summary = np.nanmean(row_diff, axis=1)

            # set nan to 0. That happens when the row is all nan
            row_diff_summary[np.isnan(row_diff_summary)] = 0

            # Compute median absolute deviation (MAD) for robust thresholding
            mad = np.median(np.abs(row_diff_summary - np.median(row_diff_summary)))

            # Identify stripe candidates where differences exceed threshold * MAD
            stripe_row = (
                row_diff_summary > np.median(row_diff_summary) + threshold * mad
            )

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

            # print(f"Band {band}: Detected {np.sum(stripe_row)} stripes.")

        return data_quality

    def _build_model(self, index: int) -> tf.keras.Model:
        """Build an autoencoder model that predicts both mean and variance. Based on arXiv:1612.01474
        :param index: Index of the model in the ensemble
        :return: Keras model
        """
        # Import locally, so we don't depend on this unless we use it
        import tensorflow as tf  # type: ignore
        from tensorflow.keras import layers, Model  # type: ignore

        tf.random.set_seed(self.seed + index)
        np.random.seed(self.seed + index)

        inputs = layers.Input(shape=(self.grid_size, self.grid_size, self.n_bands))

        # Mask missing data (0 for missing, 1 for valid)
        mask = layers.Lambda(lambda x: tf.cast(~tf.math.is_nan(x), tf.float32), output_shape=lambda s: s)(inputs)

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
        model.compile(optimizer="adam", loss=self.nll_loss)

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

        ensemble_means = np.stack(ensemble_means, axis=0)
        ensemble_vars = np.stack(ensemble_vars, axis=0)

        # Mean and var across the ensemble dimension
        mean_preds = np.mean(ensemble_means, axis=0)
        aleatoric_uncertainty = np.mean(ensemble_vars, axis=0)
        epistemic_uncertainty = np.var(ensemble_means, axis=0, ddof=1)
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
            grid = dataset[
                i - self.grid_size // 2 : i + self.grid_size // 2 + 1,
                j - self.grid_size // 2 : j + self.grid_size // 2 + 1,
                :,
            ]

            if np.any(
                missing_mask[
                    i - self.grid_size // 2 : i + self.grid_size // 2 + 1,
                    j - self.grid_size // 2 : j + self.grid_size // 2 + 1,
                    :,
                ]
                > 0
            ):
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
        missing_any_band = np.any(missing_boolean_mask, axis=2)

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
            return (np.ndarray([]), np.ndarray([]), dataset)

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
                if missing_boolean_mask[i, j, band]:
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


__all__ = [
    "EcostressAeDeepEnsembleInterpolate",
]
