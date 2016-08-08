from geocal import *
import pickle
from .pickle_method import *
import h5py
import math
from multiprocessing import Pool
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split

class L1bGeoGenerate(object):
    '''This generate a L1B geo output file from a given
    ImageGroundConnection. I imagine we will modify this as time
    goes on, this is really just a placeholder.
    '''
    def __init__(self, igc, lwm, output_name, run_config = None,
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
        self.lwm = lwm
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
        vzenith = np.empty((rcast.number_position, rcast.number_sample))
        vazimuth = np.empty((rcast.number_position, rcast.number_sample))
        szenith = np.empty((rcast.number_position, rcast.number_sample))
        sazimuth = np.empty((rcast.number_position, rcast.number_sample))
        lfrac = np.empty((rcast.number_position, rcast.number_sample))
        i = 0
        while True:
            r = rcast.next_position()
            ln = rcast.current_position - rcast.start_position
            # Take advantage of the fact that all samples have the same
            # orbit position. Not sure this is true for the real ecostress
            # camera, but for now take advantage of this. We'll probably move
            # this to C++ for performance anyways. Same thing for solar position
            ic = ImageCoordinate(rcast.current_position, 0)
            opos = self.igc.cf_look_vector_pos(ic)
            t = self.igc.pixel_time(ic)
            sollv_cf = CartesianFixedLookVector.solar_look_vector(t)
            for j in range(r.shape[1]):
                pt = Ecr(*r[0,j,0,0,0,:])
                lat[ln, j] = pt.latitude
                lon[ln, j] = pt.longitude
                height[ln, j] = pt.height_reference_surface
                vln = LnLookVector(CartesianFixedLookVector(pt, opos), pt)
                vzenith[ln,j] = vln.view_zenith
                vazimuth[ln,j] = vln.view_azimuth
                sln = LnLookVector(sollv_cf, pt)
                szenith[ln, j] = sln.view_zenith
                sazimuth[ln, j] = sln.view_azimuth
                lfrac[ln, j]= self.lwm.interpolate(self.lwm.coordinate(pt)) * 100.0
            i += 1
            if(i % 100 ==0 and print_status):
                print("Done with position %d" % i)
            if(rcast.last_position):
                break
        return lat, lon, height, vzenith, vazimuth, szenith, sazimuth, lfrac

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
        vzenith = np.hstack([rv[3] for rv in r])
        vazimuth = np.hstack([rv[4] for rv in r])
        szenith = np.hstack([rv[5] for rv in r])
        sazimuth = np.hstack([rv[6] for rv in r])
        lfrac = np.hstack([rv[7] for rv in r])
        return lat,lon,height,vzenith, vazimuth, szenith,sazimuth, lfrac

    def run(self, pool = None):
        '''Do the actual generation of data.'''
        lat, lon, height, vzenith, vazimuth, szenith, sazimuth, lfrac = \
           self.loc(pool)
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
        dt, tm = time_split(self.igc.ipi.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.igc.ipi.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm)
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
        m.write()
