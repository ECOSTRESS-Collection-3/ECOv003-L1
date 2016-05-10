import h5py
import numpy as np

class WriteStandardMetadata(object):
    '''This writes the standard metadata'''
    def __init__(self, hdf_file, product_specfic_group = b"L1GEOMetadata",
                 pge_name = b'L1B_GEO'):
        '''hdf_file should be the h5py.File handler'''
        self.hdf_file = hdf_file
        # Initialize all the data.
        self.data = {}
        for m, typ, ln in self.mlist:
            if(typ == "String"):
                self.data[m] = self.pad_string(b'dummy', ln)
            elif(typ == "Float64"):
                self.data[m] = np.float64(0.0)
            elif(typ == "Int32"):
                self.data[m] = np.int32(0)
            elif(typ == "Float32"):
                self.data[m] = np.float32(0.0)
            else:
                raise RuntimeError("Unrecognized type '%s'" % typ)
        # Fill in values we can.
        self.set('AncillaryInputPointer', product_specfic_group)
        self.set('AutomaticQualityFlag', b'PASS')
        self.set('DataFormatType', b'NCSAHDF5')
        # How do we determine these?
        self.set('HDFVersionId', b'1.8.16')
        self.set('ImageLines', 5400)
        self.set('ImageLineSpacing', 68.754)
        self.set('ImagePixels', 5400)
        self.set('ImagePixelSpacing', 65.536)
        self.set('InstrumentShortName', b'ECOSTRESS')
        self.set('LongName', b'ECOSTRESS')
        self.set('PGEName', pge_name)
        self.set('PlatformLongName', b'ISS')
        self.set('PlatformShortName', b'ISS')
        self.set('PlatformType', b'Spacecraft')
        self.set('ProcessingLevelID', b'1')
        self.set('ProcessingLevelDescription', 
                 b'Level 1 Geolocation Parameters')
        self.set('ProducerAgency', b'JPL')
        self.set('ProducerInstitution', b'Caltech')
        self.set('CampaignShortName', b'Primary')
        self.set('DayNightFlag', b'Day')

# Things we can set?
# BuildID - Have a global variable
# PGEVersion - Have a global variable
#
# EastBoundingCoordinate
# NorthBoundingCoordinate
# SouthBoundingCoordinate
# WestBoundingCoordinate
#
# RangeBeginningDate
# RangeBeginningTime
# RangeEndingDate
# RangeEndingTime
#
# LocalGranuleID
# SceneID
# StartOrbitNumber
# StopOrbitNumber
    def set(self, m, v):
        if(self.data[m] is None):
            raise RuntimeError("Key '%m' is not in standard metadata" % m)
        if(isinstance(self.data[m], np.string_)):
            self.data[m] = self.pad_string(v, len(self.data[m]))
        elif(isinstance(self.data[m], np.float64)):
            self.data[m] = np.float64(v)
        elif(isinstance(self.data[m], np.int32)):
            self.data[m] = np.int32(v)
        elif(isinstance(self.data[m], np.float32)):
            self.data[m] = np.float32(v)
        else:
            raise RuntimeError("Unrecognized type")

    def pad_string(self, s, ln):
        '''Create a fixed length string.'''
        if(len(s) > ln):
            raise RuntimeError("String '%s' is longer than allowed size %d" %(s, ln))
        if(len(s) == ln):
            return np.string_(s)
        return np.string_(s + b'\0'*(ln-len(s)))

    @property
    def mlist(self):
        return [
["AncillaryInputPointer", "String", 255],
["AutomaticQualityFlag", "String", 8],
["BuildId", "String", 8],
["CollectionLabel", "String", 255],
["DataFormatType", "String", 8],
["DayNightFlag", "String", 8],
["EastBoundingCoordinate", "Float64", 8],
["HDFVersionId", "String", 8],
["ImageLines", "Int32", 4],
["ImageLineSpacing", "Float32", 4],
["ImagePixels", "Int32", 4],
["ImagePixelSpacing", "Float32", 4],
["InputPointer", "String", 255],
["InstrumentShortName", "String", 20],
["LocalGranuleID", "String", 60],
["LongName", "String", 80],
["NorthBoundingCoordinate", "Float64", 8],
["PGEName", "String", 16],
["PGEVersion", "String", 8],
["PlatformLongName", "String", 80],
["PlatformShortName", "String", 20],
["PlatformType", "String", 20],
["ProcessingLevelID", "String", 6],
["ProcessingLevelDescription", "String", 80],
["ProcessingQAAttribute", "String", 8],
["ProcessingQADescription", "String", 8],
["ProducerAgency", "String", 80],
["ProducerInstitution", "String", 80],
["ProductionDateTime", "String", 20],
["ProductionLocation", "String", 80],
["CampaignShortName", "String", 20],
["RangeBeginningDate", "String", 8],
["RangeBeginningTime", "String", 12],
["RangeEndingDate", "String", 8],
["RangeEndingTime", "String", 12],
["SceneID", "String", 8],
["ShortName", "String", 20],
["SISName", "String", 80],
["SISVersion", "String", 8],
["SouthBoundingCoordinate", "Float64", 8],
["StartOrbitNumber", "String", 8],
["StopOrbitNumber", "String", 8],
["WestBoundingCoordinate", "Float64", 8],
            ]

    def clear_old(self, g):
        '''Clear any old metadata fields.'''
        for m, typ, ln in self.mlist:
            if(m in g):
                del g[m]
        
    def process_run_config_metadata(self, run_config):
        '''This takes a RunConfig object is fills in the metadata we can
        from this file.'''
        self.data["ShortName"] = run_config["ProductPathGroup", "ShortName"]
        self.data["ProductionDateTime"] = \
          run_config["JobIdentification", "ProductionDateTime"]
        self.data["ProductionLocation"] = \
          run_config["JobIdentification", "ProductionLocation"]
    def write(self):
        '''Actually write the metadata.'''
        if("StandardMetadata" in self.hdf_file):
            g = self.hdf_file["StandardMetadata"]
        else:
            g = self.hdf_file.create_group("StandardMetadata")
        self.clear_old(g)
        for m, typ, ln in self.mlist:
            g[m] = self.data[m]
