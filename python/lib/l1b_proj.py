from ecostress_swig import *
import geocal
import pickle
from .pickle_method import *
from multiprocessing import Pool
import numpy as np
import scipy.ndimage
import traceback
class L1bProj(object):
    '''This handles projecting a Igc to the surface, forming a vicar file
    that we can then match against. We can do this in parallel if you
    pass a pool in.'''
    def __init__(self, igccol, fname_list, ref_fname_list, ortho_base,
                 log_fname = None, number_subpixel = 2,
                 scratch_fname="initial_lat_lon.dat",
                 pass_through_error=False):
        '''Project igc and generate a Vicar file fname.'''
        self.igccol = igccol
        self.gc_arr = list()
        self.ortho_base = ortho_base
        self.ref_fname_list = ref_fname_list
        self.fname_list = fname_list
        self.log_fname = log_fname
        self.scratch_fname = scratch_fname
        self.number_subpixel = number_subpixel
        self.pass_through_error = pass_through_error
                                        
        # Want to scale to roughly 60 meters. Much of the landsat data is
        # at higher resolution, but ecostress is close to 70 meter pixel so
        # want data to roughly match
        self.ortho_scale = [round(60.0 / b.map_info.resolution_meter)
                            for b in self.ortho_base]
        for i in range(self.igccol.number_image):
            self.gc_arr.append(GroundCoordinateArray(
                self.igccol.image_ground_connection(i)))

    def print_and_log(self, s):
        print(s)
        if(self.log_fname is not None):
            self.log = open(self.log_fname, "a")
            print("INFO:L1bProj:%s" % s, file = self.log)
            self.log.flush()
            self.log = None

    def report_and_log_exception(self, igc_ind):
        print("Exception occurred while projecting %s:" % self.igccol.title(igc_ind))
        traceback.print_exc()
        print("Skipping this scene and continuing processing")
        if(self.log_fname is not None):
            self.log = open(self.log_fname, "a")
            print("INFO:L1bProj:Exception occurred while projecting %s:" % self.igccol.title(igc_ind), file = self.log)
            traceback.print_exc(file=self.log)
            print("INFO:L1bProj:Skipping projection for this scene and continuing processing", file=self.log)
            self.log.flush()
            self.log = None
            
    def scratch_file(self, create=False):
        '''Open/Create the scratch file we use in our lat/lon calculation.'''
        mode = "w+" if create else "r+"
        return np.memmap(self.scratch_fname, dtype="f8",
                         mode=mode,
                         shape=(self.igccol.number_image,
                          self.igccol.image_ground_connection(0).number_line,
                         self.igccol.image_ground_connection(0).number_sample,
                         2))

    def resample_data(self, igc_ind):
        try:
            mi = self.ortho_base[igc_ind].map_info.scale(self.ortho_scale[igc_ind],
                                                    self.ortho_scale[igc_ind])
            f = self.scratch_file()
            lat = f[igc_ind,:,:,0]
            lon = f[igc_ind,:,:,1]
            # This is bilinear interpolation
            lat = scipy.ndimage.interpolation.zoom(lat, self.number_subpixel,
                                                   order=1)
            # Detect the dateline. -200 is just to filter out any fill data,
            # is -180 with a bit of pad
            if(np.any(lon > 170) and np.any(np.logical_and(lon > -200, lon < -170))):
                raise RuntimeError("Don't currently handle crossing the date line")
            lon = scipy.ndimage.interpolation.zoom(lon, self.number_subpixel,
                                                   order=1)
            # Resample data to project to surface
            res = Resampler(lat, lon, mi, self.number_subpixel)
            # Don't need this anymore, and the data is large. So free it
            lat = None
            lon = None
            ras = self.igccol.image_ground_connection(igc_ind).image
            self.print_and_log("Starting resample for %s" % self.igccol.title(igc_ind))
            res.resample_field(self.fname_list[igc_ind], ras, 1.0, "HALF", True)
            self.print_and_log("Done with resample for %s" % self.igccol.title(igc_ind))
            self.print_and_log("Starting reference image for %s" % self.igccol.title(igc_ind))
            ortho = self.ortho_base[igc_ind]
            ortho.create_subset_file(self.ref_fname_list[igc_ind],
                                     "VICAR",
                                     Desired_map_info = res.map_info,
                                     Translate_arg = "-ot Int16")
#                                     Translate_arg = "-ot Int16",
#                                     Verbose = True)
            self.print_and_log("Done with reference image for %s" % self.igccol.title(igc_ind))
            return True
        except Exception as e:
            if(not self.pass_through_error):
                raise
            self.report_and_log_exception(igc_ind)
            return False
        
    def proj_scan(self, it):
        igc_ind, scan_index = it
        igc = self.igccol.image_ground_connection(igc_ind)
        start_line, end_line = igc.time_table.scan_index_to_line(scan_index)
        nlinescan = igc.number_line_scan
        rad = geocal.SubRasterImage(igc.image, start_line, 0, nlinescan,
                                    igc.image.number_sample)
        d = rad.read_all()
        f = self.scratch_file()
        if(np.all(d <= fill_value_threshold)):
            f[igc_ind, start_line:end_line, :, :] = -1e99
        else:
            t = self.gc_arr[igc_ind].ground_coor_scan_arr(start_line)
            f[igc_ind, start_line:end_line, :, :] = t[:,:,0,0,0:2]
        self.print_and_log("Done with [%d, %d, %d]" % (igc_ind, start_line,end_line))
        return True

    def proj(self, pool = None):
        # Create file, but then close. We reopen in each process. Without
        # this, numpy seems to create some sort of lock where only one
        # process acts at a time.
        f = self.scratch_file(create = True)
        f = None
        # Get lat/lon. We do this in parallel, processing each scan index of
        # each scene.
        it = []
        for i in range(self.igccol.number_image):
            igc = self.igccol.image_ground_connection(i)
            for j in range(igc.time_table.number_scan):
                it.append((i, j))
        if(pool is None):
            list(map(self.proj_scan, it))
        else:
            pool.map(self.proj_scan, it)

        # Now resample data, and also resample orthobase to the same
        # map projection.
        it = list(range(self.igccol.number_image))
        # Seem to run into trouble doing this in parallel, I think the
        # memory use is high enough that it causes problems. May look
        # to reduce resample_data memory use somehow. This step is quick
        # enough that this probably isn't much of an actual problem in
        # practice
        return list(map(self.resample_data, it))
        #if(pool is None):
        #    list(map(self.resample_data, it))
        #else:
        #    pool.map(self.resample_data, it)
        
__all__ = ["L1bProj"]
