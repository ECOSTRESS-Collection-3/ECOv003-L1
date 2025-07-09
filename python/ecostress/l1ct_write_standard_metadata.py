from __future__ import annotations
from .write_standard_metadata import WriteStandardMetadata
import numpy as np
from typing import Any


class L1ctWriteStandardMetadata(WriteStandardMetadata):
    """Add a few extra fields we use in l1gt"""

    def __init__(
        self,
        *args : Any,
        orbit_corrected : bool=True,
        geolocation_accuracy_qa : str="Poor",
        **kwargs : Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.orbit_corrected = orbit_corrected
        self.geolocation_accuracy_qa = geolocation_accuracy_qa
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
        self.set("GeolocationAccuracyQAExplanation",
"""Best - Image matching was performed for this scene, expect 
       good geolocation accuracy.
Good - Image matching was performed on a nearby scene, and correction 
       has been interpolated/extrapolated. Expect good geolocation accuracy.
Suspect - Matched somewhere in the orbit. Expect better geolocation 
       than orbits w/o image matching, but may still have large errors.
Poor - No matches in the orbit. Expect largest geolocation errors.
""")
        self.data["CRS"] = "fake"
        self.data["SceneBoundaryLatLonWKT"] = "fake"

    @property
    def mlist(self) -> list[tuple[str,str]]:
        m = super().mlist
        m.append(("AutomaticQualityFlagExplanation", "String"))
        m.append(("CRS", "String"))
        m.append(("SceneBoundaryLatLonWKT", "String"))
        return m

__all__ = ["L1ctWriteStandardMetadata"]
