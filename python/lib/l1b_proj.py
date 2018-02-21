from geocal import *
from ecostress_swig import *
import pickle
from .pickle_method import *
from multiprocessing import Pool

class L1bProj(object):
    '''This handles projecting a Igc to the surface, forming a vicar file
    that we can then match against. We can do this in parallel if you
    pass a pool in.'''
    def __init__(self, igc_list, fname_list):
        '''Project igc and generate a Vicar file fname.'''
        # We do 2x2 subpixeling. May need to adapt this once we figure
        # out the size we will use with Landsat data
        self.igc_list = igc_list
        self.gc_arr = list()
        self.f = list()
        for i, igc in enumerate(self.igc_list):
            self.gc_arr.append(GroundCoordinateArray(igc, False, 2, 2))
            self.f.append(self.gc_arr[i].raster_cover_vicar(fname_list[i]))
    def proj_scan(self, it):
        igc_ind, start_line, number_line = it
        self.gc_arr[igc_ind].project_surface_scan_arr(self.f[igc_ind],
                                                      start_line, number_line)
        print("Done with [%d, %d, %d]" % (igc_ind, start_line,
                                          start_line + number_line))
        return True
    def proj(self, pool = None):
        it = []
        for i, igc in enumerate(self.igc_list):
            for j in range(igc.time_table.number_scan):
                ls,le = igc.time_table.scan_index_to_line(j)
                it.append((i, ls, le-ls))
        if(pool is None):
            map(self.proj_scan, it)
        else:
            pool.map(self.proj_scan, it)
            
        
        
