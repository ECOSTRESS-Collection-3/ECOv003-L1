from __future__ import annotations
from .write_standard_metadata import WriteStandardMetadata
from typing import Any
import json
import numpy as np


class L1ctWriteStandardMetadata(WriteStandardMetadata):
    """Add a few extra fields we use in l1gt"""

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
        self.orbit_corrected = orbit_corrected
        self.geolocation_accuracy_qa = geolocation_accuracy_qa
        self.tcorr_before = tcorr_before
        self.tcorr_after = tcorr_after
        self.over_all_land_fraction = over_all_land_fraction
        self.average_solar_zenith = average_solar_zenith
        self.qa_precentage_missing = qa_precentage_missing
        self.band_specification = band_specification
        self.cal_correction = cal_correction
        if geolocation_accuracy_qa in (
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
        self.set("GeolocationAccuracyQA", self.geolocation_accuracy_qa)
        self.set(
            "GeolocationAccuracyQAExplanation",
            """Best - Image matching was performed for this scene, expect 
       good geolocation accuracy.
Good - Image matching was performed on a nearby scene, and correction 
       has been interpolated/extrapolated. Expect good geolocation accuracy.
Suspect - Matched somewhere in the orbit. Expect better geolocation 
       than orbits w/o image matching, but may still have large errors.
Poor - No matches in the orbit. Expect largest geolocation errors.
""",
        )
        self.data["CRS"] = "fake"
        self.data["SceneBoundaryLatLonWKT"] = "fake"

    @property
    def mlist(self) -> list[tuple[str, str]]:
        m = super().mlist
        m.append(("AutomaticQualityFlagExplanation", "String"))
        m.append(("CRS", "String"))
        m.append(("SceneBoundaryLatLonWKT", "String"))
        return m

    def write(self) -> None:
        super().write()
        self.write_json()

    def write_json(self) -> None:
        if self.json_file is None:
            raise RuntimeError("Need json_file to call write_json")
        fh = open(self.json_file, "w")
        jdict: dict[str, dict[str, int | str | float | list[float]]] = {}
        jdict["StandardMetadata"] = {}
        jdict["ProductMetadata"] = {"AncillaryFiles": 0}
        pg = jdict["ProductMetadata"]
        pg["OrbitCorrectionPerformed"] = "True" if self.orbit_corrected else "False"
        pg["GeolocationAccuracyQA"] = self.geolocation_accuracy_qa
        pg["DeltaTimeOfCorrectionBeforeScene"] = float(self.tcorr_before)
        pg["DeltaTimeOfCorrectionAfterScene"] = float(self.tcorr_after)
        txt = """Best - Image matching was performed for this scene, expect 
       good geolocation accuracy.
Good - Image matching was performed on a nearby scene, and correction 
       has been interpolated/extrapolated. Expect good geolocation accuracy.
Suspect - Matched somewhere in the orbit. Expect better geolocation 
       than orbits w/o image matching, but may still have large errors.
Poor - No matches in the orbit. Expect largest geolocation errors.
"""
        pg["GeolocationAccuracyQAExplanation"] = txt
        pg["AverageSolarZenith"] = float(self.average_solar_zenith)
        pg["OverAllLandFraction"] = float(self.over_all_land_fraction)
        if self.cal_correction is None:
            raise RuntimeError("Need cal_correction to call write")
        pg["CalibrationGainCorrection"] = list(self.cal_correction[0, :].astype(float))
        pg["CalibrationOffsetCorrection"] = list(
            self.cal_correction[1, :].astype(float)
        )
        klist = sorted([m for m, _ in self.mlist])
        for m in klist:
            d = self.data[m]
            if isinstance(d, np.int32):
                d = int(d)
            elif isinstance(d, np.int64):
                d = int(d)
            elif isinstance(d, np.float32):
                d = float(d)
            elif isinstance(d, np.float64):
                d = float(d)
            if d is not None:
                jdict["StandardMetadata"][m] = d
        print(json.dumps(jdict, indent=2), file=fh)
        fh.close()


__all__ = ["L1ctWriteStandardMetadata"]
