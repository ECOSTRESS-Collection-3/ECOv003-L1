import numpy as np
import h5py
import subprocess
from .misc import time_split
import os

class L0Simulate(object):
    '''This is used to generate L0 simulated data. We take the output of the
    l1a_raw pge and reverse the processing to produce a L0 file.'''
    def __init__(self, l1a_raw_att_fname, l1a_eng_fname, scene_files):
        '''Create a L0Simulate to process the given files. The orbit based files
        are passed in as a file name, and the scene based files are passed as a dict
        with keys of scene id. The values in the dict are an array, the first entry
        is the L1A_RAW_PIX file and the second is the L1A_BB file.
        '''
        self.l1a_eng_fname = l1a_eng_fname
        self.l1a_raw_att_fname = l1a_raw_att_fname
        self.scene_files = scene_files

    def hdf_copy(self, fname, group, group_out = None, scene = None):
        '''Copy the given group from the give file to our output file.
        Default it to give the output the same group name, but can change this. If
        scene is passed in, we nest the output by "Scene_<num>"'''
        if(group_out is None):
            if(scene is not None):
                group_out = "/Data/Scene_%d%s" % (scene, group)
            else:
                group_out = "/Data" + group
        subprocess.run(["h5copy", "-i", fname, "-o", self.l0_fname, "-p",
                        "-s", group,
                        "-d", group_out], check=True)
            
        
    def create_file(self, l0_fname):
        self.l0_fname = l0_fname
        try:
            os.unlink(self.l0_fname)
        except OSError:
            pass
        self.hdf_copy(self.l1a_eng_fname, "/rtdBlackbodyGradients")
        self.hdf_copy(self.l1a_raw_att_fname, "/Attitude")
        self.hdf_copy(self.l1a_raw_att_fname, "/Ephemeris")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/StartOrbitNumber")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeBeginningTime")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeBeginningDate")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeEndingTime")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeEndingDate")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeBeginningTime",
                      group_out = "/StandardMetadata/RangeBeginningTime")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeBeginningDate",
                      group_out = "/StandardMetadata/RangeBeginningDate")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeEndingTime",
                      group_out = "/StandardMetadata/RangeEndingTime")
        self.hdf_copy(self.l1a_raw_att_fname, "/StandardMetadata/RangeEndingDate",
                      group_out = "/StandardMetadata/RangeEndingDate")
        for scene, v in self.scene_files.items():
            l1a_raw_pix_fname, l1a_bb_fname = v
            self.hdf_copy(l1a_raw_pix_fname, "/UncalibratedPixels", scene=int(scene))
            self.hdf_copy(l1a_raw_pix_fname, "/StandardMetadata/RangeBeginningTime",
                          scene=int(scene))
            self.hdf_copy(l1a_raw_pix_fname, "/StandardMetadata/RangeBeginningDate",
                          scene=int(scene))
            self.hdf_copy(l1a_raw_pix_fname, "/StandardMetadata/RangeEndingTime",
                          scene=int(scene))
            self.hdf_copy(l1a_raw_pix_fname, "/StandardMetadata/RangeEndingDate",
                          scene=int(scene))
            self.hdf_copy(l1a_bb_fname, "/BlackBodyPixels", scene=int(scene))
            
        






