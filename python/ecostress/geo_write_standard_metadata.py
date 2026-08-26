from __future__ import annotations
from .write_standard_metadata import WriteStandardMetadata
from typing import Any


class GeoWriteStandardMetadata(WriteStandardMetadata):
    """Add a few extra fields we use in l1b_geo"""

    def __init__(
        self,
        *args: Any,
        orbit_corrected: bool = True,
        tcorr_before: float = -9999,
        tcorr_after: float = -9999,
        geolocation_accuracy_qa: str = "Poor",
        geolocation_number_tiepoint: int = 0,
        geolocation_tiepoint_ce68: float = -9999,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.orbit_corrected = orbit_corrected
        self.geolocation_accuracy_qa = geolocation_accuracy_qa
        self.tcorr_before = tcorr_before
        self.tcorr_after = tcorr_after
        if tcorr_before <= -9990:
            self.delta_time = self.tcorr_after
        elif tcorr_after <= -9990:
            self.delta_time = self.tcorr_before
        else:
            self.delta_time = min(self.tcorr_before, self.tcorr_after)
        self.geolocation_number_tiepoint = geolocation_number_tiepoint
        self.geolocation_tiepoint_ce68 = geolocation_tiepoint_ce68
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
        if self.hdf_file is None:
            raise RuntimeError("Need hdf_file to call write")
        g = self.hdf_file["StandardMetadata"]
        pg = self.hdf_file[self.product_specfic_group]
        pg["OrbitCorrectionPerformed"] = "True" if self.orbit_corrected else "False"
        if not self.orbit_based:
            pg["GeolocationAccuracyQA"] = self.geolocation_accuracy_qa
            g["GeolocationAccuracyQA"] = self.geolocation_accuracy_qa
            pg["GeolocationNumberTiepoint"] = self.geolocation_number_tiepoint
            g["GeolocationNumberTiepoint"] = self.geolocation_number_tiepoint
            pg["GeolocationDeltaTimeCorrection"] = self.delta_time
            g["GeolocationDeltaTimeCorrection"] = self.delta_time
            pg["GeolocationTiepointCE68"] = self.geolocation_tiepoint_ce68
            g["GeolocationTiepointCE68"] = self.geolocation_tiepoint_ce68
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


__all__ = ["GeoWriteStandardMetadata"]
