from geocal import *
import pickle
import ecostress.pickle_method
import h5py
import math
import re
from multiprocessing import Pool
from ecostress.write_standard_metadata import WriteStandardMetadata

class L1bGeoGenerate(object):
    '''This generate a L1B geo output file from a given
    ImageGroundConnection. I imagine we will modify this as time
    goes on, this is really just a placeholder.
    '''
    def __init__(self, igc, output_name, run_config = None,
                 start_line = 0,
                 number_line = -1,
                 number_integration_step = 1,
                 raycast_resolution = 100, 
                 max_height=10e3,
                 local_granule_id = None):
        '''Create a L1bGeoGenerate with the given ImageGroundConnection
        and output file name. To actually generate, execute the 'run'
        command.

        You can pass the run_config in which is used to fill in some of the 
        metadata. Without this, we skip that metadata and just have fill data.
        This is useful for testing, but for production you'll always want to 
        have the run config available.'''
        self.igc = igc
        self.output_name = output_name
        self.start_line = start_line
        self.number_line = number_line
        self.number_integration_step = number_integration_step
        self.raycast_resolution = raycast_resolution
        self.max_height = max_height
        self.run_config = run_config
        self.local_granule_id = local_granule_id

    def loc_parallel_func(self, it):
        '''Variation of loc that is easier to use with a multiprocessor pool.'''
        # Handle number_sample too large here, so we don't have to
        # have special handling elsewhere
        start_sample = it[0]
        nleft = self.igc.number_sample - start_sample
        number_sample = min(it[1], nleft)
        rcast = IgcRayCaster(self.igc, self.start_line,
                             self.number_line, self.number_integration_step,
                             self.raycast_resolution, self.max_height, 
                             start_sample,
                             number_sample)
        # Only print status if we are the last job started, just so 
        # we don't get a confusing mishmash of lots of jobs.
        print_status = False
        if(start_sample + number_sample == self.igc.number_sample):
            print_status = True
        if(print_status):
            print("Have %d positions to calculate" % rcast.number_position)
        lat = np.empty((rcast.number_position, rcast.number_sample))
        lon = np.empty((rcast.number_position, rcast.number_sample))
        height = np.empty((rcast.number_position, rcast.number_sample))
        i = 0
        while True:
            r = rcast.next_position()
            ln = rcast.current_position - rcast.start_position
            for j in range(r.shape[1]):
                pt = Ecr(*r[0,j,0,0,0,:])
                lat[ln, j] = pt.latitude
                lon[ln, j] = pt.longitude
                height[ln, j] = pt.height_reference_surface
            i += 1
            if(i % 100 ==0 and print_status):
                print("Done with position %d" % i)
            if(rcast.last_position):
                break
        return lat, lon, height

    def loc(self, pool = None):
        '''Determine locations'''
        if(pool is None):
            return self.loc_parallel_func([0,self.igc.number_sample])
        nprocess = pool._processes
        n = math.floor(self.igc.number_sample / nprocess)
        if(self.igc.number_sample % nprocess > 0):
            n += 1
        it = [[i,n] for i in range(0,self.igc.number_sample, n)]
        r = pool.map(self.loc_parallel_func, it)
        lat = np.hstack([rv[0] for rv in r])
        lon = np.hstack([rv[1] for rv in r])
        height = np.hstack([rv[2] for rv in r])
        return lat,lon,height

    def run(self, pool = None):
        '''Do the actual generation of data.'''
        lat, lon, height = self.loc(pool)
        fout = h5py.File(self.output_name, "w")
        m = WriteStandardMetadata(fout,
                                  product_specfic_group = "L1GEOMetadata",
                                  pge_name="L1B_GEO",
                                  build_id = '0.01', pge_version='0.01',
                                  local_granule_id = self.local_granule_id)
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
        m.set("WestBoundingCoordinate", lon[lon > -998].min())
        m.set("EastBoundingCoordinate", lon[lon > -998].max())
        m.set("SouthBoundingCoordinate", lat[lat > -998].min())
        m.set("NorthBoundingCoordinate", lat[lat > -998].max())
        mt = re.match(r'(.*)T(.*)Z', str(self.igc.ipi.min_time))
        m.set("RangeBeginningDate", mt.group(1))
        m.set("RangeBeginningTime", mt.group(2))
        mt = re.match(r'(.*)T(.*)Z', str(self.igc.ipi.min_time))
        m.set("RangeEndingDate", mt.group(1))
        m.set("RangeEndingTime", mt.group(2))
        g = fout.create_group("L1bGeo")
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
        t = g.create_dataset("height", data=height/1e3, dtype='f4')
        t.attrs["Units"] = "km"
        dummy = np.empty(height.shape)
        dummy[:,:] = -9999.0
        t = g.create_dataset("view zenith", data=dummy, dtype='f4')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("view azimuth", data=dummy, dtype='f4')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("solar zenith", data=dummy, dtype='f4')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("solar azimuth", data=dummy, dtype='f4')
        t.attrs["Units"] = "degrees"
        m.write()
