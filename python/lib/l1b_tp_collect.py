from .l1b_proj import L1bProj
import geocal
import pickle
from .pickle_method import *
from multiprocessing import Pool

class L1bTpCollect(object):
    '''This is used to collect tiepoints between the ecostress data and
    our Landsat orthobase.'''
    def __init__(self, igccol, ortho_base, fftsize=256, magnify=4.0,
                 magmin=2.0, toler=1.5, redo=36, ffthalf=2, seed=562,
                 num_x=10,num_y=10, log_fname = None,
                 proj_number_subpixel=2):
        self.igccol = igccol
        self.ortho_base = ortho_base
        self.num_x=num_x
        self.num_y=num_y
        self.proj_fname = ["proj_initial_%d.img" % (i + 1) for i in range(self.igccol.number_image)]
        self.ref_fname = ["ref_%d.img" % (i + 1) for i in range(self.igccol.number_image)]
        self.log_file = ["tpmatch_%d.log" % (i + 1) for i in range(self.igccol.number_image)]
        self.run_dir_name = ["tpmatch_%d" % (i + 1) for i in range(self.igccol.number_image)]
        self.log_fname = log_fname
        self.p = L1bProj(self.igccol, self.proj_fname, self.ref_fname,
                         self.ortho_base, log_fname = self.log_fname,
                         number_subpixel=proj_number_subpixel)
        self.tpcollect = geocal.TiePointCollectPicmtch(self.igccol,
                              self.proj_fname, image_index1=0,
                              ref_image_fname=self.ref_fname[0],
                              fftsize=fftsize, magnify=magnify, magmin=magmin,
                              toler=toler,redo=redo,ffthalf=2,seed=562,
                              log_file=self.log_file[0],
                              run_dir_name=self.run_dir_name[0])

    def tp(self, i):
        '''Get tiepoints for the given scene number'''
        self.tpcollect.image_index1 = i
        self.tpcollect.ref_image_fname = self.ref_fname[i]
        self.tpcollect.log_file = self.log_file[i]
        self.tpcollect.run_dir_name = self.run_dir_name[i]
        print("Collecting tp for scene %d" % (i+1))
        if(self.log_fname is not None):
            self.log = open(self.log_fname, "a")
            print("INFO:L1bTpCollect:Collecting tp for scene %d" % (i+1),
                  file = self.log)
            self.log.flush()
        res = self.tpcollect.tie_point_grid(self.num_x, self.num_y)
        print("Done collecting tp for scene %d" % (i+1))
        if(self.log_fname is not None):
            self.log = open(self.log_fname, "a")
            print("INFO:L1bTpCollect:Done collecting tp for scene %d" % (i+1),
                  file = self.log)
            self.log.flush()
        return res
    
    def tpcol(self, pool=None):
        '''Return tiepoints collected.'''
        # First project all the data.
        self.p.proj(pool=pool)
        it = list(range(self.igccol.number_image))
        if(pool is None):
            tpcollist = map(self.tp, it)
        else:
            tpcollist = pool.map(self.tp, it)
        res = geocal.TiePointCollection()
        for tpcol in tpcollist:
            res.extend(tpcol)
        for i in range(len(res)):
            res[i].id = i+1
        return res

