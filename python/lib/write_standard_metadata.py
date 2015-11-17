import h5py
import numpy as np

class WriteStandardMetadata(object):
    '''This writes the standard metadata'''
    def __init__(self, hdf_file):
        '''hdf_file should be the h5py.File handler'''
        self.hdf_file = hdf_file
        # Initialize all the data.
        self.data = {}
        for m in self.mlist:
            self.data[m] = "placeholder"
        # Replace a few items that aren't strings.
        self.data["InputPointer"] = ["placeholder", "placeholder",
                                     "placeholder", "placeholder",
                                     "placeholder"]
        self.data["SizeMBECSDataGranule"] = np.float32(1.0)
        self.data["StartOrbitNumber"] = np.int32(1)
        self.data["StopOrbitNumber"] = np.int32(1)
        self.data["InstrumentShortName"] = "ECOSTRESS"
        self.data["PlatformLongName"] = "International Space Station"
        self.data["PlatformShortName"] = "ISS"
        self.data["PlatformType"] = "spacecraft"
        self.data["ProducerAgency"] = "NASA"
        self.data["ProducerInstitution"] = "JPL"
        self.data["ProjectId"] = "ECOSTRESS"

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
        if("Metadata" in self.hdf_file):
            g = self.hdf_file["Metadata"]
        else:
            g = self.hdf_file.create_group("Metadata")
        self.clear_old(g)
        for m in self.mlist:
            g[m] = self.data[m]
