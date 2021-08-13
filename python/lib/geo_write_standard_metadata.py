from .write_standard_metadata import *

class GeoWriteStandardMetadata(WriteStandardMetadata):
    '''Add a few extra fields we use in l1b_geo'''
    def __init__(self, *args, orbit_corrected=True, tcorr_before = -9999,
                 tcorr_after = -9999, geolocation_accuracy_qa = "No match",
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.orbit_corrected=orbit_corrected
        self.geolocation_accuracy_qa = geolocation_accuracy_qa
        self.tcorr_before = tcorr_before
        self.tcorr_after = tcorr_after
        if((self.orbit_based and orbit_corrected) or
           geolocation_accuracy_qa in ("Best", "Good")):
            self.data["AutomaticQualityFlagExplanation"] = "Image matching performed to correct orbit ephemeris/attitude"
        else:
            self.data["AutomaticQualityFlag"] = "Suspect"
            self.data["AutomaticQualityFlagExplanation"] = "Image matching was not successful correcting orbit ephemeris/attitude. Ephemeris/attitude may have significant errors."
            
    @property
    def mlist(self):
        m = super().mlist
        m.append(['AutomaticQualityFlagExplanation', "String"])
        return m

    def write(self):
        super().write()
        pg = self.hdf_file[self.product_specfic_group]
        pg["OrbitCorrectionPerformed"] = "True" if self.orbit_corrected else "False"
        if(not self.orbit_based):
            pg["GeolocationAccuracyQA"] = self.geolocation_accuracy_qa
            pg["DeltaTimeOfCorrectionBeforeScene"] = self.tcorr_before
            pg["DeltaTimeOfCorrectionAfterScene"] = self.tcorr_before
        
__all__ = ["GeoWriteStandardMetadata"]
