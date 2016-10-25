from geocal import *
import pickle
from .pickle_method import *
from multiprocessing import Pool
import h5py
from .write_standard_metadata import WriteStandardMetadata
from .misc import time_split

class L1bRadSimulate(object):
    '''This is used to generate simulated input data for the L1bGeoGenerate 
    process, for use in testing.'''
    def __init__(self, orbit, time_table, camera, surface_image, dem = None,
                 number_integration_step = 1, raycast_resolution = -1):
        '''Create a L1bGeoSimulate that works with the given orbit, time table,
        camera, and surface images. surface_image should have one image for each band.

        The default DEM to use is the SRTM, but you can pass in a different DEM if 
        desired.

        The default resolution is whatever the underlying surface image is at, but 
        you can specify a different resolution. Note that this has a strong impact
        on how long the data takes to generate. The ASTER data is 15 meter resolution,
        which means that the 70 meter ecostress pixels takes 5 x 5 subpixels. For
        a much quicker simulation, you can set this to something like 100 meters.'''
        self.orbit = orbit
        self.time_table = time_table
        self.camera = camera
        self.surface_image = surface_image
        self.dem = dem
        self.number_integration_step = number_integration_step
        self.raycast_resolution = raycast_resolution
        if(self.dem is None):
            # False here says we use a height of 0 for missing tiles, useful
            # for data that is partially over the ocean
            self.dem = SrtmDem("", False)

    def create_file(self, l1b_rad_fname, pool = None):
        fout = h5py.File(l1b_rad_fname, "w")
        g = fout.create_group("Radiance")
        g2 = fout.create_group("SWIR")
        for b in range(6):
        # We hold camera_band to 0 for now. We'll improve this and use actually
        # other bands in the future as we flesh out the simulation.
            if(b != 5):
                t = g.create_dataset("radiance_%d" % (b + 1),
                                     data = self.image(b, camera_band = 0,
                                           pool = pool).astype(np.float32))
                t.attrs["Units"] = "W/m^2/sr/um"
            else:
                t = g2.create_dataset("swir_dn",
                                      data = self.image(b, camera_band = 0,
                                           pool = pool).astype(np.uint16))
                t.attrs["Units"] = "dimensionless"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1B_RADMetadata",
                                  pge_name = "L1B_RAD_PGE")
        dt, tm = time_split(self.time_table.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.time_table.max_time)
        m.set("RangeEndingDate", dt) 
        m.set("RangeEndingTime", tm)
        m.write()
        fout.close()
                
    def image_parallel_func(self, it):
        '''Calculate image for a subset of the data, suitable for use with a
        multiprocessor pool.'''
        # Handle number_sample too large here, so we don't have to
        # have special handling elsewhere
        start_sample = it[0]
        nleft = self.igc_ray_cast.number_sample - start_sample
        number_sample = min(it[1], nleft)
        return self.igc_ray_cast.read_double(0, start_sample, self.igc_ray_cast.number_line, number_sample)
    
    def image(self, band, camera_band = None, pool = None):
        '''Use raycasting to generate a image for the given band. By default the
        camera_band is the same as the band, but you can optionally set it to a
        different value.

        Note that this takes about 5 minutes over ASTER data, using 20 processors
        (at 15 meter resolution)'''
        print("Doing band %d" % (band + 1))
        if(camera_band is None):
            camera_band = band
        ipi = Ipi(self.orbit, self.camera, camera_band, self.time_table.min_time,
                  self.time_table.max_time, self.time_table)
        igc = IpiImageGroundConnection(ipi, self.dem, None)
        self.igc_ray_cast = IgcSimulatedRayCaster(igc, self.surface_image[band],
                                                  self.number_integration_step,
                                                  self.raycast_resolution)
        if(pool is None):
            return self.image_parallel_func([0,self.igc_ray_cast.number_sample])
        nprocess = pool._processes
        n = math.floor(self.igc_ray_cast.number_sample / nprocess)
        if(self.igc_ray_cast.number_sample % nprocess > 0):
            n += 1
        it = [[i,n] for i in range(0,self.igc_ray_cast.number_sample, n)]
        r = pool.map(self.image_parallel_func, it)
        r = np.hstack(r)
        r[r < 0] = 0
        return r

        
