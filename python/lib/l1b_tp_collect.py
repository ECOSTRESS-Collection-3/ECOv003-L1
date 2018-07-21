from .l1b_proj import L1bProj
import geocal
import pickle
from .pickle_method import *
from multiprocessing import Pool
import traceback

class L1bTpCollect(object):
    '''This is used to collect tiepoints between the ecostress data and
    our Landsat orthobase.'''
    def __init__(self, igccol, ortho_base, fftsize=256, magnify=4.0,
                 magmin=2.0, toler=1.5, redo=36, ffthalf=2, seed=562,
                 num_x=10,num_y=10, log_fname = None,
                 proj_number_subpixel=2, min_tp_per_scene=20):
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
                         number_subpixel=proj_number_subpixel,
                         pass_through_error=True)
        self.tpcollect = geocal.TiePointCollectPicmtch(self.igccol,
                              self.proj_fname, image_index1=0,
                              ref_image_fname=self.ref_fname[0],
                              fftsize=fftsize, magnify=magnify, magmin=magmin,
                              toler=toler,redo=redo,ffthalf=2,seed=562,
                              log_file=self.log_file[0],
                              run_dir_name=self.run_dir_name[0])
        self.min_tp_per_scene = min_tp_per_scene

    def print_and_log(self, s):
        print(s)
        if(self.log_fname is not None):
            self.log = open(self.log_fname, "a")
            print("INFO:L1bTpCollect:%s" % s, file = self.log)
            self.log.flush()
            self.log = None

    def report_and_log_exception(self, i):
        print("Exception occurred while collecting tie-points for scene %d:" % (i+1))
        traceback.print_exc()
        print("Skipping tie-points for this scene and continuing processing")
        if(self.log_fname is not None):
            self.log = open(self.log_fname, "a")
            print("INFO:L1bTpCollect:Exception occurred while collecting tie-points for scene %d:" % (i+1), file = self.log)
            traceback.print_exc(file=self.log)
            print("INFO:L1bTpCollect:Skipping tie-points for this scene and continuing processing", file=self.log)
            self.log.flush()
            self.log = None
            
    def tp(self, i):
        '''Get tiepoints for the given scene number'''
        try:
            self.tpcollect.image_index1 = i
            self.tpcollect.ref_image_fname = self.ref_fname[i]
            self.tpcollect.log_file = self.log_file[i]
            self.tpcollect.run_dir_name = self.run_dir_name[i]
            tt = self.igccol.image_ground_connection(i).time_table
            self.print_and_log("Collecting tp for scene %d" % (i+1))
            res = self.tpcollect.tie_point_grid(self.num_x, self.num_y)
            if(len(res) < self.min_tp_per_scene):
                self.print_and_log("Too few tie-point found. Found %d, and require at least %d. Rejecting tie-points for scene %d" % (len(res), self.min_tp_per_scene, i+1))
                res = []
            else:
                self.print_and_log("Found %d tie-points for scene %d" % (len(res), i+1))
            self.print_and_log("Done collecting tp for scene %d" % (i+1))
        except Exception as e:
            self.report_and_log_exception(i)
            res = []
        return res, tt.min_time, tt.max_time
    
    def tpcol(self, pool=None):
        '''Return tiepoints collected. We also return the time ranges for the
           ImageGroundConnection that we got good tiepoint for. This
           can be used by the calling program to determine such things
           as the breakpoints on the orbit model
        '''
        
        # First project all the data.
        proj_res = self.p.proj(pool=pool)
        it = []
        for i in range(self.igccol.number_image):
            if(proj_res[i]):
                it.append(i)
        if(pool is None):
            tpcollist = map(self.tp, it)
        else:
            tpcollist = pool.map(self.tp, it)
        res = geocal.TiePointCollection()
        time_range_tp = []
        for tpcol, tmin, tmax in tpcollist:
            if(len(tpcol) > 0):
                res.extend(tpcol)
                time_range_tp.append([tmin, tmax])
        for i in range(len(res)):
            res[i].id = i+1
        return res, time_range_tp

