from ecostress_swig import *
import geocal
import pickle
from .pickle_method import *
from multiprocessing import Pool

class L1bProj(object):
    '''This handles projecting a Igc to the surface, forming a vicar file
    that we can then match against. We can do this in parallel if you
    pass a pool in.'''
    def __init__(self, igc_list, fname_list, ref_fname_list, ortho_base):
        '''Project igc and generate a Vicar file fname.'''
        # We do 2x2 subpixeling. May need to adapt this once we figure
        # out the size we will use with Landsat data
        self.igc_list = igc_list
        self.gc_arr = list()
        self.f = list()
        self.ortho_base = ortho_base
        self.ref_fname_list = ref_fname_list
        for i, igc in enumerate(self.igc_list):
            self.gc_arr.append(GroundCoordinateArray(igc, False, 2, 2))
            self.f.append(self.gc_arr[i].raster_cover_vicar(fname_list[i],
                                          self.ortho_base.map_info))
    def proj_scan(self, it):
        igc_ind, start_line, number_line = it
        self.gc_arr[igc_ind].project_surface_scan_arr(self.f[igc_ind],
                                                      start_line, number_line)
        print("Done with [%d, %d, %d]" % (igc_ind, start_line,
                                          start_line + number_line))
        return True
    def proj(self, pool = None):
        it = []
        for i, bf in enumerate(self.f):
            pt = []
            for ln in (0.5, bf.number_line - 1.5):
                for smp in (0.5, bf.number_sample - 1.5):
                    pt.append(bf.ground_coordinate(geocal.ImageCoordinate(ln,
                                                                          smp)))
            self.ortho_base.create_subset_file(self.ref_fname_list[i], "VICAR",
                                               pt, Type = "Int16")
        for i, igc in enumerate(self.igc_list):
            for j in range(igc.time_table.number_scan):
                ls,le = igc.time_table.scan_index_to_line(j)
                it.append((i, ls, le-ls))
        if(pool is None):
            map(self.proj_scan, it)
        else:
            pool.map(self.proj_scan, it)
            
        
        
__all__ = ["L1bProj"]
