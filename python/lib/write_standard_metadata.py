import h5py
import numpy as np
import os
import re
import copy

class WriteStandardMetadata(object):
    '''This writes the standard metadata'''
    def __init__(self, hdf_file, product_specfic_group = "L1GEOMetadata",
                 proc_lev_desc = 'Level 1 Geolocation Parameters',
                 pge_name = 'L1B_GEO', local_granule_id = None,
                 build_id = '0.01', pge_version='0.01',
                 qa_precentage_missing = None,
                 band_specification = None,
                 orbit_based = False, level0_file = False):
        '''hdf_file should be the h5py.File handler. You can pass the 
        local_granule_id, or if None we assume the filename for the hdf_file is
        the local_granule_id'''
        self.hdf_file = hdf_file
        self.product_specfic_group = product_specfic_group
        if(local_granule_id is None):
            local_granule_id = os.path.basename(hdf_file.filename)

        # Initialize all the data.
        self.data = {}
        for m, typ in self.mlist:
            if(typ == "String"):
                self.data[m] = 'dummy'
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
        self.set('AutomaticQualityFlag', 'PASS')
        self.set('CampaignShortName', 'Primary')
        self.set('CollectionLabel', '')
        self.set('DataFormatType', 'NCSAHDF5')
        # How do we determine these?
        self.set('HDFVersionID', '1.8.16')
        self.set('ImageLines', 5400)
        self.set('ImageLineSpacing', 68.754)
        self.set('ImagePixels', 5400)
        self.set('ImagePixelSpacing', 65.536)

        self.set('InstrumentShortName', 'ECOSTRESS')
        self.set('LongName', 'ECOSTRESS')
        self.set('PGEName', pge_name)
        self.set('PlatformLongName', 'ISS')
        self.set('PlatformShortName', 'ISS')
        self.set('PlatformType', 'Spacecraft')
        self.set('ProcessingLevelDescription', proc_lev_desc )
        self.set('ProducerAgency', 'JPL')
        self.set('ProducerInstitution', 'Caltech')
        self.set('CampaignShortName', 'Primary')
        self.set('RegionID', '')
        self.set('DayNightFlag', 'NA')
        self.set('SISName', "Level 1 Product Specification Document (JPL D-94634)")
        self.set('SISVersion', "Preliminary")
        self.set('BuildID', build_id)
        self.set('PGEVersion', pge_version)
        self.set('LocalGranuleID', local_granule_id)
        # For now parse the local granule id to get some of the metadata.
        # Might get this from the run config file instead
        if(level0_file):
            # Can't set the next bit, so skip it
            return
        elif(orbit_based):
            m = re.match(r'(ECOSTRESS_)?(?P<process_level>\w+)_(\w+)_(?P<orbit>\d{5})_', local_granule_id)
        else:
            m = re.match(r'(ECOSTRESS_)?(?P<process_level>\w+)_(\w+)_(?P<orbit>\d{5})_(?P<scene_id>\d{3})', local_granule_id)
        if(not m):
            raise RuntimeError("Unrecognized local granule id '%s'" % 
                               local_granule_id)
        self.set('StartOrbitNumber', m.group('orbit'))
        self.set('StopOrbitNumber', m.group('orbit'))
        if(orbit_based):
            self.set('SceneID', "NA")
        else:
            self.set('SceneID', m.group('scene_id'))
        self.set('ProcessingLevelID', m.group('process_level'))
        self.qa_precentage_missing = qa_precentage_missing
        self.band_specification = band_specification

    def set_input_pointer(self, flist):
        '''Take a list of file names, and generates the InputPointer from this'''
        self.set('InputPointer', ",".join(os.path.basename(i) for i in flist))
       
    def set(self, m, v):
        if(self.data[m] is None):
            raise RuntimeError("Key '%m' is not in standard metadata" % m)
        if(isinstance(self.data[m], bytes) or
           isinstance(self.data[m], str)):
            self.data[m] = v
        elif(isinstance(self.data[m], np.float64)):
            self.data[m] = np.float64(v)
        elif(isinstance(self.data[m], np.int32)):
            self.data[m] = np.int32(v)
        elif(isinstance(self.data[m], np.float32)):
            self.data[m] = np.float32(v)
        else:
            raise RuntimeError("Unrecognized type")

    def pad_string(self, s, ln):
        '''Create a fixed length string. Note not currently used, but we'll 
        leave the function here in case we end up needing it.'''
        if(len(s) > ln):
            raise RuntimeError("String '%s' is longer than allowed size %d" %(s, ln))
        if(len(s) == ln):
            return np.string_(s)
        return np.string_(s + b'\0'*(ln-len(s)))

    @property
    def mlist(self):
        return [
["AncillaryInputPointer", "String"],
["AutomaticQualityFlag", "String"],
["BuildID", "String"],
["CollectionLabel", "String"],
["DataFormatType", "String"],
["DayNightFlag", "String"],
["EastBoundingCoordinate", "Float64"],
["HDFVersionID", "String"],
["ImageLines", "Int32"],
["ImageLineSpacing", "Float32"],
["ImagePixels", "Int32"],
["ImagePixelSpacing", "Float32"],
["InputPointer", "String"],
["InstrumentShortName", "String"],
["LocalGranuleID", "String"],
["LongName", "String"],
["NorthBoundingCoordinate", "Float64"],
["PGEName", "String"],
["PGEVersion", "String"],
["PlatformLongName", "String"],
["PlatformShortName", "String"],
["PlatformType", "String"],
["ProcessingLevelID", "String"],
["ProcessingLevelDescription", "String"],
["ProducerAgency", "String"],
["ProducerInstitution", "String"],
["ProductionDateTime", "String"],
["ProductionLocation", "String"],
["CampaignShortName", "String"],
["RangeBeginningDate", "String"],
["RangeBeginningTime", "String"],
["RangeEndingDate", "String"],
["RangeEndingTime", "String"],
["RegionID", "String"],
["SceneID", "String"],
["ShortName", "String"],
["SISName", "String"],
["SISVersion", "String"],
["SouthBoundingCoordinate", "Float64"],
["StartOrbitNumber", "String"],
["StopOrbitNumber", "String"],
["WestBoundingCoordinate", "Float64"],
            ]

    def clear_old(self, g):
        '''Clear any old metadata fields.'''
        for m, typ in self.mlist:
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

    def copy_new_file(self, hdf_file, local_granule_id, short_name):
        '''Copy metadata, applying to a different file'''
        h = self.hdf_file
        self.hdf_file = None
        mcopy = copy.deepcopy(self)
        self.hdf_file = h
        mcopy.hdf_file = hdf_file
        mcopy.local_granule_id = local_granule_id
        mcopy.set('LocalGranuleID', local_granule_id)
        mcopy.set("ShortName", short_name)
        return mcopy
    
    def write(self):
        '''Actually write the metadata.'''
        if("StandardMetadata" in self.hdf_file):
            g = self.hdf_file["StandardMetadata"]
        else:
            g = self.hdf_file.create_group("StandardMetadata")
        self.clear_old(g)
        for m, typ in self.mlist:
            g[m] = self.data[m]
        if(self.product_specfic_group in self.hdf_file):
            pg = self.hdf_file[self.product_specfic_group]
        else:
            pg = self.hdf_file.create_group(self.product_specfic_group)
        pg["AncillaryFiles"] = np.int32(0)
        if(self.qa_precentage_missing is not None):
            pg["QAPercentMissingData"] = np.float32(self.qa_precentage_missing)
            pg["QAPercentMissingData"].attrs['Units']="percentage"
            pg["QAPercentMissingData"].attrs['valid_min'] = 0
            pg["QAPercentMissingData"].attrs['valid_max'] = 100
        if(self.band_specification is not None):
            pg.create_dataset('BandSpecification', data=self.band_specification,
                              dtype=np.float32)
            pg['BandSpecification'].attrs["Units"] = "micrometer"
            pg['BandSpecification'].attrs["valid_min"] = 1.6
            pg['BandSpecification'].attrs["valid_max"] = 12.1
            pg['BandSpecification'].attrs["fill"] = 0
            
        

__all__ = ["WriteStandardMetadata"]
