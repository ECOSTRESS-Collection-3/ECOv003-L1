from geocal import *
from ecostress_swig import *
import pickle
from .pickle_method import *
from multiprocessing import Pool

class L1bProj(object):
    '''This handles projecting a Igc to the surface, forming a vicar file
    that we can then match against. We can do this in parallel if you
    pass a pool in.'''
    def __init__(self, igc, fname):
        '''Project igc and generate a Vicar file fname.'''
        # We do 2x2 subpixeling. May need to adapt this once we figure
        # out the size we will use with Landsat data
        self.igc = igc
        self.gc_arr = GroundCoordinateArray(igc, False, 2, 2)
        self.f = self.gc_arr.raster_cover_vicar(fname)
    def proj_scan(self, it):
        start_line, number_line = it
        self.gc_arr.project_surface_scan_arr(self.f, start_line, number_line)
        print("Done with [%d, %d]" % (start_line, start_line + number_line))
        return True
    def proj(self, pool = None):
        it = []
        for i in range(self.igc.time_table.number_scan):
            ls,le = self.igc.time_table.scan_index_to_line(i)
            it.append((ls, le-ls))
        if(pool is None):
            map(self.proj_scan, it)
        else:
            pool.map(self.proj_scan, it)
            
        
        
