from __future__ import annotations
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    FILL_VALUE_BAD_OR_MISSING,
    FILL_VALUE_STRIPED,
    FILL_VALUE_NOT_SEEN,
    DQI_BAD_OR_MISSING,
    DQI_STRIPE_NOT_INTERPOLATED,
    DQI_NOT_SEEN,
    DQI_GOOD,
    EcostressRadApply,
    EcostressRadAverage,
    fill_value_threshold,
    band_to_band_tie_points,
    GeometricModelImageHandleFill,
)
import h5py  # type: ignore
from .rad_write_standard_metadata import RadWriteStandardMetadata
from .misc import is_day
from .ecostress_interpolate import (
    EcostressAeDeepEnsembleInterpolate,
    EcostressLocalWindowKNNInterpolator,
)
import numpy as np
from loguru import logger
import typing
from typing import Any

if typing.TYPE_CHECKING:
    from .run_config import RunConfig


class L1bRadGenerate(object):
    """This generates a L1B rad file from the given L1A_PIX file."""

    def __init__(
        self,
        igc: geocal.ImageGroundConnection,
        l1a_pix: str,
        l1a_gain: str,
        output_name: str,
        l1_osp_dir: str,
        cal_correction: np.ndarray,
        interpolator_parameters: dict[str, Any] | None = None,
        local_granule_id: str | None = None,
        run_config: None | RunConfig = None,
        build_id: str = "0.30",
        collection_label: str = "ECOSTRESS",
        pge_version: str = "0.30",
        interpolate_stripe_data: bool = False,
        find_horizontal_stripes: bool = True,
        seed: int = 1234,
        line_order_flipped: bool = False,
        skip_band_to_band: bool = False,
        frac_to_do_interpolation: float = 0.3,
    ) -> None:
        """Create a L1bRadGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command."""
        self.igc = igc
        self.l1a_pix_fname = l1a_pix
        self.l1a_pix = h5py.File(l1a_pix, "r")
        if "BandSpecification" in self.l1a_pix["L1A_PIXMetadata"]:
            self.nband = int(
                np.count_nonzero(
                    self.l1a_pix["L1A_PIXMetadata/BandSpecification"][:] > 0
                )
            )
            # The earliest data still had the SWIR on. So we might see "6".
            # For the purpose of EcostressAeDeepEnsembleInterpolate, this is
            # the same as 5 bands - the SWIR is never used. Adjust this
            # so EcostressAeDeepEnsembleInterpolate isn't confused by getting a "6"
            if self.nband > 5:
                self.nband = 5
        else:
            self.nband - 6
        if interpolator_parameters is None:
            self.interpolator_parameters = {}
        else:
            self.interpolator_parameters = interpolator_parameters
        self.l1a_gain_fname = l1a_gain
        self.output_name = output_name
        self.local_granule_id = local_granule_id
        self.l1_osp_dir = l1_osp_dir
        self.run_config = run_config
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version
        self.interpolate_stripe_data = interpolate_stripe_data
        self.find_horizontal_stripes = find_horizontal_stripes
        self.seed = seed
        self.skip_band_to_band = skip_band_to_band
        self.total_possible_scan = 0
        self.missing_scan = 0
        self.frac_to_do_interpolation = frac_to_do_interpolation
        self.line_order_flipped = line_order_flipped
        self.cal_correction = cal_correction

    def image(self, band: int) -> np.ndarray:
        """Generate L1B_RAD image.

        This applies the gains from L1A_PIX to scale to radiance data.

        We use a quadratic transformation to do band to band registration.
        """

        rad = EcostressRadApply(self.l1a_pix_fname, self.l1a_gain_fname, band)
        res = np.empty((int(rad.number_line / 2), rad.number_sample), dtype=np.float32)
        nscan = int(rad.number_line / self.igc.number_line_scan)
        for scan_index in range(nscan):
            logger.debug(f"Doing scan_index {scan_index} for band {band}")
            # Perform band to band, unless we have been directed to skip
            # it (useful for initial working on band to band registration
            sline = scan_index * self.igc.number_line_scan
            nlinescan = self.igc.number_line_scan
            radsub = geocal.SubRasterImage(rad, sline, 0, nlinescan, rad.number_sample)
            d = radsub.read_all()
            # Skip processing scan if all the data is bad. This allows
            # handling for short scenes, where we might not have the
            # L1A_ATT data to calculate band to band.
            self.total_possible_scan += 1
            if np.all(d <= fill_value_threshold):
                res[int(sline / 2) : int((sline + nlinescan) / 2), :] = (
                    FILL_VALUE_BAD_OR_MISSING
                )
                self.missing_scan += 1
            else:
                if not self.skip_band_to_band:
                    tplist = band_to_band_tie_points(self.igc, scan_index, band)
                    m = geocal.QuadraticGeometricModel()
                    m.fit_transformation(tplist)
                    fill_value = FILL_VALUE_NOT_SEEN
                    rbreg = GeometricModelImageHandleFill(
                        radsub, m, radsub.number_line, radsub.number_sample, fill_value
                    )
                    rbreg_avg = EcostressRadAverage(rbreg)
                else:
                    rbreg_avg = EcostressRadAverage(radsub)
                if self.line_order_flipped:
                    res[int(sline / 2) : int((sline + nlinescan) / 2), :] = np.flipud(
                        rbreg_avg.read_all_double()
                    )
                else:
                    res[int(sline / 2) : int((sline + nlinescan) / 2), :] = (
                        rbreg_avg.read_all_double()
                    )
        # We don't actually correct SWIR.
        # self.cal_correction is 2 x band, where first entry is gain and second
        # if offset
        if band != 0:
            res = np.where(
                res <= fill_value_threshold,
                res,
                self.cal_correction[0, band - 1] * res
                + self.cal_correction[1, band - 1],
            )
        return res

    def run(self) -> None:
        """Do the actual generation of data."""
        fout = h5py.File(self.output_name, "w")
        # Get all data and DQI first, so we can
        self.total_possible_scan = 0
        self.missing_scan = 0
        for b in range(5):
            data = self.image(b + 1)
            if b == 0:
                dataset = np.empty((*data.shape, 5))
                dqi = np.zeros(dataset.shape, dtype=np.int8)
            dataset[:, :, b] = data
        inter_uncer = np.zeros(dataset.shape)
        dqi[dataset == FILL_VALUE_NOT_SEEN] = DQI_NOT_SEEN
        dqi[dataset == FILL_VALUE_STRIPED] = DQI_STRIPE_NOT_INTERPOLATED
        dqi[dataset == FILL_VALUE_BAD_OR_MISSING] = DQI_BAD_OR_MISSING
        dataset, inter_uncer, dqi = self.interpolate_missing(dataset, inter_uncer, dqi)
        g = fout.create_group("Radiance")
        for b in range(5):
            t = g.create_dataset(
                "radiance_%d" % (b + 1),
                data=dataset[:, :, b],
                dtype="f4",
                fillvalue=FILL_VALUE_BAD_OR_MISSING,
                compression="gzip",
            )
            t.attrs.create("_FillValue", data=FILL_VALUE_BAD_OR_MISSING, dtype=t.dtype)
            t.attrs["Units"] = "W/m^2/sr/um"
            t = g.create_dataset(
                "interpolation_uncertainty_%d" % (b + 1),
                data=inter_uncer[:, :, b],
                dtype="f4",
                fillvalue=0.0,
                compression="gzip",
            )
            t.attrs.create("_FillValue", data=0.0, dtype=t.dtype)
            t.attrs["Units"] = "W/m^2/sr/um"
            t.attrs["Description"] = """
Uncertainty in the interpolated value for data that
we interpolated (so data_quality has value DQI_INTERPOLATED).

See ATB for details.
            
Set to 0.0 for values that we haven't interpolated.
"""
            t = g.create_dataset(
                "data_quality_%d" % (b + 1), data=dqi[:, :, b], compression="gzip"
            )
            t.attrs["valid_min"] = 0
            t.attrs["valid_max"] = 4
            t.attrs["Description"] = """
Data quality indicator. 
  0 - DQI_GOOD, normal data, nothing wrong with it
  1 - DQI_INTERPOLATED, data was part of instrument 
      'stripe', and we have filled this in with 
      interpolated data (see ATB) 
  2 - DQI_STRIPE_NOT_INTERPOLATED, data was part of
      instrument 'stripe' and we could not fill in
      with interpolated data.
  3 - DQI_BAD_OR_MISSING, indicates data with a bad 
      value (e.g., negative DN) or missing packets.
  4 - DQI_NOT_SEEN, pixels where because of the 
      difference in time that a sample is seen with 
      each band, the ISS has moved enough we haven't 
      seen the pixel. So data is missing, but by
      instrument design instead of some problem.
"""
            t.attrs["Units"] = "dimensionless"

        g = fout.create_group("SWIR")
        data_swir = self.image(0).astype(np.int16)
        t = g.create_dataset(
            "swir_dn",
            data=data_swir,
            fillvalue=FILL_VALUE_BAD_OR_MISSING,
            compression="gzip",
        )
        t.attrs.create("_FillValue", data=FILL_VALUE_BAD_OR_MISSING, dtype=t.dtype)
        t.attrs["Units"] = "dimensionless"
        g = fout.create_group("Time")
        t = g.create_dataset(
            "line_start_time_j2000",
            data=self.l1a_pix["Time/line_start_time_j2000"][0::2],
        )
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        g = fout.create_group("FPIEencoder")
        t = g.create_dataset(
            "EncoderValue", data=self.l1a_pix["/FPIEencoder/EncoderValue"]
        )
        t.attrs["Description"] = "Mirror encoder value of each focal plane in each scan"
        t.attrs["Units"] = "dimensionless"
        t.attrs["valid_min"] = 0
        t.attrs["valid_max"] = 1749247
        t.attrs["fill"] = 0xFFFFFFFF
        qa_precentage_missing = -999
        if "QAPercentMissingData" in self.l1a_pix["L1A_PIXMetadata"]:
            qa_precentage_missing = self.l1a_pix[
                "L1A_PIXMetadata/QAPercentMissingData"
            ][()]
        band_specification = [1.6, 8.2, 8.7, 9.0, 10.5, 12.0]
        if "BandSpecification" in self.l1a_pix["L1A_PIXMetadata"]:
            band_specification = self.l1a_pix["L1A_PIXMetadata/BandSpecification"][:]
        m = RadWriteStandardMetadata(
            fout,
            product_specfic_group="L1B_RADMetadata",
            proc_lev_desc="Level 1B Radiance Parameters",
            pge_name="L1B_RAD_PGE",
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version,
            line_order_flipped=self.line_order_flipped,
            local_granule_id=self.local_granule_id,
            qa_precentage_missing=qa_precentage_missing,
            band_specification=band_specification,
            cal_correction=self.cal_correction,
        )
        if self.run_config is not None:
            m.process_run_config_metadata(self.run_config)
        m.set(
            "RangeBeginningDate",
            self.l1a_pix["/StandardMetadata/RangeBeginningDate"][()],
        )
        m.set(
            "RangeBeginningTime",
            self.l1a_pix["/StandardMetadata/RangeBeginningTime"][()],
        )
        m.set("RangeEndingDate", self.l1a_pix["/StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime", self.l1a_pix["/StandardMetadata/RangeEndingTime"][()])
        # Short term allow this to fail, just so we can process old data
        # which didn't have FieldOfViewObstruction (added in B7)
        try:
            m.set(
                "FieldOfViewObstruction",
                self.l1a_pix["/StandardMetadata/FieldOfViewObstruction"][()],
            )
        except KeyError:
            pass
        m.set("ImageLines", data_swir.shape[0])
        m.set("ImagePixels", data_swir.shape[1])
        m.set("DayNightFlag", "Day" if is_day(self.igc) else "Night")
        m.set_input_pointer(
            [
                self.l1a_pix_fname,
                self.l1a_gain_fname,
                self.l1_osp_dir + "/l1b_rad_config.py",
            ]
        )
        m.write()

    def interpolate_missing(
        self, dataset: np.ndarray, inter_uncer: np.ndarray, dqi: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Interpolate missing data. We pull this out, just because it is a bit long
        and it makes run above a little cleaner"""
        # Only do interpolation if we are directed to,
        # and we have enough data present (e.g., skip
        # if too little of the scene actually has imagery)
        frac_data_present = (
            self.total_possible_scan - self.missing_scan
        ) / self.total_possible_scan
        if (
            self.interpolate_stripe_data
            and frac_data_present < self.frac_to_do_interpolation
        ):
            logger.info(
                "Skipping interpolation because fraction of scans present is too small (e.g., short scene)"
            )
            return dataset, inter_uncer, dqi
        elif not self.interpolate_stripe_data:
            return dataset, inter_uncer, dqi

        if False:
            # Old interpolator
            inter = EcostressAeDeepEnsembleInterpolate(
                seed=self.seed,
                n_bands=self.nband,
                verbose=False,
                grid_size=self.interpolator_parameters.get("grid_size", 1),
                latent_dim=self.interpolator_parameters.get("latent_dim", 16),
                encoder_layers=self.interpolator_parameters.get("encoder_layers", [32]),
                decoder_layers=self.interpolator_parameters.get("decoder_layers", [32]),
                activation=self.interpolator_parameters.get("activation", "elu"),
                n_ensemble=self.interpolator_parameters.get("n_ensemble", 3),
                n_good_bands_required=self.interpolator_parameters.get(
                    "n_good_bands_required", 2
                ),
            )
        else:
            # New interpolator
            inter = EcostressLocalWindowKNNInterpolator(
                n_bands=self.nband,
                # must be odd
                window_size=self.interpolator_parameters.get("window_size", 201),
                n_neighbors=self.interpolator_parameters.get("n_neighbors", 10),
                max_train_samples=self.interpolator_parameters.get(
                    "max_train_samples", 5000
                ),
                min_feature_bands_for_prediction=self.interpolator_parameters.get(
                    "min_feature_bands_for_prediction", 2
                ),
                max_feature_bands_for_prediction=self.interpolator_parameters.get(
                    "max_feature_bands_for_prediction", 3
                ),
                feature_selection_scope=self.interpolator_parameters.get(
                    "feature_selection_scope", "center"
                ),
                random_state=self.interpolator_parameters.get("random_state", 1234),
                min_train_per_window=self.interpolator_parameters.get(
                    "min_train_per_window", 15
                ),
                block_step=self.interpolator_parameters.get("block_step", None),
                inner_size=self.interpolator_parameters.get("inner_size", None),
                knn_n_jobs=self.interpolator_parameters.get("knn_n_jobs", 1),
                exclude_full_bad_edge_columns=self.interpolator_parameters.get(
                    "exclude_full_bad_edge_columns", True
                ),
                allow_relaxed_center_drop=self.interpolator_parameters.get(
                    "allow_relaxed_center_drop", True
                ),
                center_drop_max_fraction=self.interpolator_parameters.get(
                    "center_drop_max_fraction", 0.10
                ),
            )

        # identify horizontal stripes and update data quality mask (if turned on)
        if self.find_horizontal_stripes:
            dqi = inter.find_horizontal_stripes(
                dataset,
                dqi,
                threshold=self.interpolator_parameters.get("horizontal_threshold", 5),
            )

        # Prediction apparently doesn't work with negative radiance. We can
        # actually legitimately have negative radiance (physical radiance isn't,
        # but measured can be if we happen to have a small DN). But this isn't
        # overly important, so just go ahead and filter out before we do our training
        # and fill in.
        if np.any((dataset < 0) & (dqi == DQI_GOOD)):
            logger.info(
                "Found negative radiances with good DQI. Setting to FILL_VALUE_BAD_OR_MISSING"
            )
            dqi[(dataset < 0) & (dqi == DQI_GOOD)] = DQI_BAD_OR_MISSING
            dataset[(dataset < 0) & (dqi == DQI_GOOD)] = FILL_VALUE_BAD_OR_MISSING

        if False:
            # New interpolator doesn't need training
            logger.info("Starting model training")
            inter.train(
                dataset,
                dqi,
                epochs=self.interpolator_parameters.get("epochs", 25),
                batch_size=self.interpolator_parameters.get("batch_size", 32),
                n_samples=self.interpolator_parameters.get("n_samples", 100_000),
                validate=self.interpolator_parameters.get("validate", False),
                validate_threshold=self.interpolator_parameters.get(
                    "validate_threshold", 5
                ),
            )
        logger.info("Interpolating missing data")
        return inter.interpolate_missing(dataset, dqi)


__all__ = ["L1bRadGenerate"]
