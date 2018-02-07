import numpy as np
import h5py
from .write_standard_metadata import WriteStandardMetadata
from .misc import ecostress_radiance_scale_factor, time_split
from ecostress_swig import *
from geocal import ImageCoordinate

class L1aPixSimulate(object):
    '''This is used to generate L1A_PIX simulated data from a L1B_RAD file.
    This is the inverse of the l1b_rad_generate process.'''
    def __init__(self, igc, surface_image):
        '''Create a L1APixSimulate to process the given 
        EcostressImageGroundConnection.  We supply the surface map projected 
        image as an array, one entry per band in the igc.'''
        self.igc = igc
        self.surface_image = surface_image

    def image_parallel_func(self, it):
        '''Calculate image for a subset of data.'''
        return self.sim_rad.radiance_scan(it[0], it[1])
        
    def image(self, band, pool = None):
        '''Generate a l1a pix image for the given band.'''
        print("Doing band %d" % (band + 1))
        self.igc.band = band
        # Don't bother averaging data, just use the center pixel. Since we
        # are simulated, this should be find and is much faster.
        avg_fact = 1
        self.sim_rad = SimulatedRadiance(GroundCoordinateArray(self.igc),
                                         self.surface_image[band], avg_fact)
        it = [[i,256] for i in range(0, self.igc.number_line, 256)]
        if(pool):
            r = pool.map(self.image_parallel_func, it)
        else:
            r = map(self.image_parallel_func, it)
        r = np.vstack(r)
        # Don't think we have any negative data, but go ahead and zero this out
        # if there is any
        r[r<0] = 0
        # Note we can change this to work with gain and offset if we want
        # to test this functionality. But for now we use the same DN that
        # the ASTER data is in, so no scaling is needed.
        r = r.astype(np.int16)
        return r

    def create_file(self, l1a_pix_fname, pool = None):
        fout = h5py.File(l1a_pix_fname, "w")
        g = fout.create_group("UncalibratedDN")
        for b in range(6):
            t = g.create_dataset("b%d_image" % (b + 1),
                                 data = self.image(b, pool=pool))
            t.attrs["Units"] = "dimensionless"
        g = fout.create_group("Time")
        t = g.create_dataset("line_start_time_j2000",
         data=np.array([self.igc.time_table.time(ImageCoordinate(i, 0))[0].j2000
                        for i in range(self.igc.time_table.max_line + 1)]),
                             dtype='f8')
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        m = WriteStandardMetadata(fout, product_specfic_group = "L1A_PIXMetadata",
                                  pge_name = "L1A_CAL_PGE")
        dt, tm = time_split(self.igc.time_table.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(self.igc.time_table.max_time)
        m.set("RangeEndingDate", dt) 
        m.set("RangeEndingTime", tm)
        m.write()
        fout.close()







