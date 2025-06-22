from .write_standard_metadata import WriteStandardMetadata


class GeoWriteStandardMetadata(WriteStandardMetadata):
    """Add a few extra fields we use in l1b_geo"""

    def __init__(
        self,
        *args,
        orbit_corrected=True,
        tcorr_before=-9999,
        tcorr_after=-9999,
        geolocation_accuracy_qa="Poor",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.orbit_corrected = orbit_corrected
        self.geolocation_accuracy_qa = geolocation_accuracy_qa
        self.tcorr_before = tcorr_before
        self.tcorr_after = tcorr_after
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
    def mlist(self):
        m = super().mlist
        m.append(["AutomaticQualityFlagExplanation", "String"])
        return m

    def write(self):
        super().write()
        g = self.hdf_file["StandardMetadata"]
        pg = self.hdf_file[self.product_specfic_group]
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


__all__ = ["GeoWriteStandardMetadata"]
