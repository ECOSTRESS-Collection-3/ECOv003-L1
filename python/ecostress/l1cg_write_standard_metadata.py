from __future__ import annotations
from .write_standard_metadata import WriteStandardMetadata
import numpy as np
from typing import Any


class L1cgWriteStandardMetadata(WriteStandardMetadata):
    """Add a few extra fields we use in l1gc"""

    def __init__(
        self,
        *args: Any,
        orbit_corrected: bool = True,
        tcorr_before: float = -9999,
        tcorr_after: float = -9999,
        over_all_land_fraction: float = 0.0,
        average_solar_zenith: float = 0.0,
        geolocation_accuracy_qa: str = "Poor",
        qa_precentage_missing: float | None = None,
        band_specification: None | list[float] = None,
        cal_correction: None | np.ndarray = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.hdfeos_file = True
        self.orbit_corrected = orbit_corrected
        self.geolocation_accuracy_qa = geolocation_accuracy_qa
        self.tcorr_before = tcorr_before
        self.tcorr_after = tcorr_after
        self.over_all_land_fraction = over_all_land_fraction
        self.average_solar_zenith = average_solar_zenith
        self.qa_precentage_missing = qa_precentage_missing
        self.band_specification = band_specification
        self.cal_correction = cal_correction
        if (self.orbit_based and orbit_corrected) or geolocation_accuracy_qa in (
            "Best",
            "Good",
        ):
            self.data["AutomaticQualityFlagExplanation"] = (
                "Image matching performed to correct orbit ephemeris/attitude"
            )
        else:
            self.data["AutomaticQualityFlag"] = "Suspect"
            self.data["AutomaticQualityFlagExplanation"] = (
                "Image matching was not successful correcting scene ephemeris/attitude. Ephemeris/attitude may have significant errors."
            )

    @property
    def mlist(self) -> list[tuple[str, str]]:
        m = super().mlist
        m.append(("AutomaticQualityFlagExplanation", "String"))
        return m

    def write(self) -> None:
        super().write()
        g = self.hdf_file["/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES/StandardMetadata"]
        pg = self.hdf_file[
            f"/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES/{self.product_specfic_group}"
        ]
        pg["OrbitCorrectionPerformed"] = "True" if self.orbit_corrected else "False"
        if not self.orbit_based:
            pg["GeolocationAccuracyQA"] = self.geolocation_accuracy_qa
            g["GeolocationAccuracyQA"] = self.geolocation_accuracy_qa
            pg["DeltaTimeOfCorrectionBeforeScene"] = self.tcorr_before
            pg["DeltaTimeOfCorrectionAfterScene"] = self.tcorr_after
            txt = """Best - Image matching was performed for this scene, expect 
       good geolocation accuracy.
Good - Image matching was performed on a nearby scene, and correction 
       has been interpolated/extrapolated. Expect good geolocation accuracy.
Suspect - Matched somewhere in the orbit. Expect better geolocation 
       than orbits w/o image matching, but may still have large errors.
Poor - No matches in the orbit. Expect largest geolocation errors.
"""
            pg["GeolocationAccuracyQAExplanation"] = txt
            g["GeolocationAccuracyQAExplanation"] = txt
            d = pg.create_dataset("AverageSolarZenith", data=self.average_solar_zenith)
            d.attrs["Units"] = "degrees"
            d.attrs["valid_min"] = -90
            d.attrs["valid_max"] = 90
            d.attrs["Description"] = "Average solar zenith angle for scene"
            d = pg.create_dataset(
                "OverAllLandFraction", data=self.over_all_land_fraction
            )
            d.attrs["Units"] = "percentage"
            d.attrs["valid_min"] = 0
            d.attrs["valid_max"] = 100
            d.attrs["Description"] = "Overall land fraction for scene"
            if self.cal_correction is not None:
                d = pg.create_dataset(
                    "CalibrationGainCorrection",
                    data=self.cal_correction[0, :],
                    dtype=np.float32,
                )
                d.attrs["Units"] = "dimensionless"
                d = pg.create_dataset(
                    "CalibrationOffsetCorrection",
                    data=self.cal_correction[1, :],
                    dtype=np.float32,
                )
                d.attrs["Units"] = "W/m^2/sr/um"


__all__ = ["L1cgWriteStandardMetadata"]
