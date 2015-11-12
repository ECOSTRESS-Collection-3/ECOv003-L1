import h5py
import numpy as np

class WriteStandardMetadata(object):
    '''This writes the standard metadata'''
    def __init__(self, hdf_file):
        '''hdf_file should be the h5py.File handler'''
        self.hdf_file = hdf_file

    @property
    def mlist(self):
        return [
            "AncillaryDataDescriptors",
            "AutomaticQualityFlag",
            "BuildId",
            "CollectionLabel",
            "DataFormatType",
            "GranuleName",
            "HDFVersionId",
            "InputPointer",
            "InstrumentShortName",
            "ProductTypeLongName",
            "PlatformLongName",
            "PlatformShortName",
            "PlatformType",
            "ProcessingLevel",
            "ProducerAgency",
            "ProducerInstitution",
            "ProductionDateTime",
            "ProductionLocation",
            "ProjectId",
            "RangeBeginningDate",
            "RangeBeginningTime",
            "RangeEndingDate",
            "RangeEndingTime",
            "ShortName",
            "SISName",
            "SISVersion",
            "SizeMBECSDataGranule",
            "StartOrbitNumber",
            "StopOrbitNumber",
            ]

    def clear_old(self, g):
        '''Clear any old metadata fields.'''
        for m in self.mlist:
            if(m in g):
                del g[m]
        
    def write(self):
        '''Actually write the metadata.'''
        if("Metadata" in self.hdf_file):
            g = self.hdf_file["Metadata"]
        else:
            g = self.hdf_file.create_group("Metadata")
        self.clear_old(g)
        g["AncillaryDataDescriptors"] = "placeholder"
        g["AutomaticQualityFlag"] = "placeholder"
        g["BuildId"] = "placeholder"
        g["CollectionLabel"] = "placeholder"
        g["DataFormatType"] = "placeholder"
        g["GranuleName"] = "placeholder"
        g["HDFVersionId"] = "placeholder"
        g["InputPointer"] = ["placeholder", "placeholder", "placeholder", 
                             "placeholder", "placeholder"]
        g["InstrumentShortName"] = "placeholder"
        g["ProductTypeLongName"] = "placeholder"
        g["PlatformLongName"] = "placeholder"
        g["PlatformShortName"] = "placeholder"
        g["PlatformType"] = "placeholder"
        g["ProcessingLevel"] = "placeholder"
        g["ProducerAgency"] = "placeholder"
        g["ProducerInstitution"] = "placeholder"
        g["ProductionDateTime"] = "placeholder"
        g["ProductionLocation"] = "placeholder"
        g["ProjectId"] = "placeholder"
        g["RangeBeginningDate"] = "placeholder"
        g["RangeBeginningTime"] = "placeholder"
        g["RangeEndingDate"] = "placeholder"
        g["RangeEndingTime"] = "placeholder"
        g["ShortName"] = "placeholder"
        g["SISName"] = "placeholder"
        g["SISVersion"] = "placeholder"
        g["SizeMBECSDataGranule"] = np.float32(1.0)
        g["StartOrbitNumber"] = np.int32(1)
        g["StopOrbitNumber"] = np.int32(1)
