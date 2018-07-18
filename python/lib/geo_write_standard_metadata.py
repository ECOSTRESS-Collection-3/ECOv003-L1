from .write_standard_metadata import *

class GeoWriteStandardMetadata(WriteStandardMetadata):
    '''Add a few extra fields we use in l1b_geo'''
    def __init__(self, *args, orbit_corrected=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.orbit_corrected=orbit_corrected
        if(self.orbit_corrected):
            self.data["AutomaticQualityFlagExplanation"] = "Image matching performed to correct orbit ephemeris/attitude"
        else:
            self.data["AutomaticQualityFlag"] = "Suspect"
            self.data["AutomaticQualityFlagExplanation"] = "Image matching was not successful correcting orbit ephemeris/attitude. Using original ISS supplied ephemeris/attitude which may have significant errors."
            
    @property
    def mlist(self):
        m = super().mlist
        m.append(['AutomaticQualityFlagExplanation', "String"])
        return m

    def write(self):
        super().write()
        pg = self.hdf_file[self.product_specfic_group]
        pg["OrbitCorrectionPerformed"] = "True" if self.orbit_corrected else "False"
        
__all__ = ["GeoWriteStandardMetadata"]
