import geocal
from ecostress_swig import *
import pickle
from .pickle_method import *
import h5py
import math
from multiprocessing import Pool
from .geo_write_standard_metadata import GeoWriteStandardMetadata
from .misc import time_split
import numpy as np

class L1bGeoGenerate(object):
    '''This generate a L1B geo output file from a given ImageGroundConnection.
    '''
    def __init__(self, igc, lwm, output_name, inlist, is_day,
                 run_config = None,
                 start_line = 0,
                 number_line = -1,
                 local_granule_id = None, log_fname = None,
                 build_id = "0.30",
                 pge_version = "0.30",
                 correction_done = True):
        '''Create a L1bGeoGenerate with the given ImageGroundConnection
        and output file name. To actually generate, execute the "run"
        command.

        You can pass the run_config in which is used to fill in some of the 
        metadata. Without this, we skip that metadata and just have fill data.
        This is useful for testing, but for production you will always want to 
        have the run config available.'''
        self.igc = igc
        self.gc_arr = GroundCoordinateArray(self.igc, True)
        self.lwm = lwm
        self.is_day = is_day
        self.output_name = output_name
        self.start_line = start_line
        self.number_line = number_line
        self.run_config = run_config
        self.local_granule_id = local_granule_id
        self.log_fname = log_fname
        self.log = None
        self.build_id = build_id
        self.pge_version = pge_version
        self.inlist = inlist
        self.correction_done = correction_done

    def loc_parallel_func(self, it):
        '''Variation of loc that is easier to use with a multiprocessor pool.'''
        start_line, number_line = it
        try:
            # Note res here refers to an internal cache array of gc_arr
            res = self.gc_arr.ground_coor_scan_arr(start_line, number_line)
            print("Done with [%d, %d]" % (start_line, start_line+res.shape[0]))
            if(self.log_fname is not None):
                self.log = open(self.log_fname, "a")
                print("INFO:L1bGeoGenerate:Done with [%d, %d]" %
                      (start_line, start_line+res.shape[0]), file = self.log)
                self.log.flush()
        except RuntimeError:
            res = np.empty((number_line, self.igc.image.number_sample, 1, 1, 7))
            res[:] = FILL_VALUE_BAD_OR_MISSING
            print("Skipping [%d, %d]" % (start_line, start_line+res.shape[0]))
            if(self.log_fname is not None):
                self.log = open(self.log_fname, "a")
                print("INFO:L1bGeoGenerate:Skipping [%d, %d]" %
                      (start_line, start_line+res.shape[0]), file = self.log)
                self.log.flush()
        # Note the copy() here is very important. As an optimization,
        # ground_coor_scan_arr return a reference to an internal cache
        # variable. This array gets overwritten in the next call to
        # ground_coor_scan_arr. So we need to explicitly copy anything
        # we want to keep.
        lat = res[:,:,0,0,0].copy()
        lon = res[:,:,0,0,1].copy()
        height = res[:,:,0,0,2].copy()
        vzenith = res[:,:,0,0,3].copy()
        vazimuth = res[:,:,0,0,4].copy()
        szenith = res[:,:,0,0,5].copy()
        sazimuth = res[:,:,0,0,6].copy()
        lfrac = GroundCoordinateArray.interpolate(self.lwm, lat, lon) * 100.0
        tlinestart = np.array([self.igc.pixel_time(geocal.ImageCoordinate(ln, 0)).j2000 for ln in range(start_line, start_line+res.shape[0])])
        return (lat, lon, height, vzenith, vazimuth, szenith, sazimuth,
                lfrac, tlinestart)

    def loc(self, pool = None):
        '''Determine locations'''
        it = []
        for i in range(self.igc.time_table.number_scan):
            ls,le = self.igc.time_table.scan_index_to_line(i)
            le2 = self.start_line + self.number_line
            if(self.start_line < le and (self.number_line == -1 or le2 >= ls)):
                if(self.number_line == -1):
                    it.append((ls,le-ls))
                else:
                    it.append((ls,min(le-ls,le2-ls)))
        if(pool is None):
            r = list(map(self.loc_parallel_func, it))
        else:
            r = pool.map(self.loc_parallel_func, it)
        lat = np.vstack([rv[0] for rv in r])
        lon = np.vstack([rv[1] for rv in r])
        height = np.vstack([rv[2] for rv in r])
        vzenith = np.vstack([rv[3] for rv in r])
        vazimuth = np.vstack([rv[4] for rv in r])
        szenith = np.vstack([rv[5] for rv in r])
        sazimuth = np.vstack([rv[6] for rv in r])
        lfrac = np.vstack([rv[7] for rv in r])
        tlinestart = np.hstack([rv[8] for rv in r])
        return lat,lon,height,vzenith, vazimuth, szenith,sazimuth, lfrac, \
            tlinestart

    def run(self, pool = None):
        '''Do the actual generation of data.'''
        lat, lon, height, vzenith, vazimuth, szenith, sazimuth, lfrac, \
            tlinestart = self.loc(pool)
        fout = h5py.File(self.output_name, "w")
        m = GeoWriteStandardMetadata(fout,
                                  product_specfic_group = "L1GEOMetadata",
                                  proc_lev_desc = "Level 1B Geolocation Parameters",                                  
                                  pge_name="L1B_GEO",
                                  build_id = self.build_id,
                                  pge_version= self.pge_version,
                                  orbit_corrected=self.correction_done,
                                  local_granule_id = self.local_granule_id)
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
        m.set("WestBoundingCoordinate", lon[lon > -998].min())
        m.set("EastBoundingCoordinate", lon[lon > -998].max())
        m.set("SouthBoundingCoordinate", lat[lat > -998].min())
        m.set("NorthBoundingCoordinate", lat[lat > -998].max())
        m.set("ImageLines", lat.shape[0])
        m.set("ImagePixels", lat.shape[1])
        dt, tm = time_split(self.igc.time_table.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.igc.time_table.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm)
        m.set("DayNightFlag", "Day" if self.is_day else "Night")
        m.set_input_pointer(self.inlist)
        g = fout.create_group("Geolocation")
        g.attrs["Projection"] = '''\
The latitude, longitude, and height are relative to the WGS-84
ellipsoid. Specifically the projection used is described by
the Well-Known Text (WKT):

GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
'''
        g.attrs["Projection_WKT"] = '''\
GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
'''
        # Compression doesn't seem to do a lot, so leave turned off. We can always
        # turn this on if needed.
        #t = g.create_dataset("latitude", data=lat, chunks=(250,250), compression="gzip")
        t = g.create_dataset("latitude", data=lat, dtype='f8')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("longitude", data=lon, dtype='f8')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("height", data=height, dtype='f4')
        t.attrs["Units"] = "m"
        t = g.create_dataset("land_fraction", data=lfrac, dtype='f4')
        t.attrs["Units"] = "percentage"
        t = g.create_dataset("view_zenith", data=vzenith, dtype='f4')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("view_azimuth", data=vazimuth, dtype='f4')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("solar_zenith", data=szenith, dtype='f4')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("solar_azimuth", data=sazimuth, dtype='f4')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("line_start_time_j2000", data=tlinestart,
                             dtype='f8')
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        m.write()

__all__ = ["L1bGeoGenerate"]
