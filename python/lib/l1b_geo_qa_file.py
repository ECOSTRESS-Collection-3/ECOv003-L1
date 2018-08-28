import h5py
import os

class L1bGeoQaFile(object):
    '''This is the L1bGeoQaFile. We have a separate class just to make it
    easier to interface with.'''
    def __init__(self, fname, log_fname, local_granule_id = None):
        self.fname = fname
        self.log_fname = log_fname
        if(local_granule_id):
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(fname)
        # This ends up getting pickled, and h5py doesn't pickle well. So
        # instead of keeping the file open, we reopen and update as needed.
        
        fout = h5py.File(fname, "w")
        log_group = fout.create_group("Logs")
        tplog_group = log_group.create_group("Tiepoint Logs")
        fout.close()
        
    def add_tp_log(self, scene_name, tplogfname):
        '''Add a TP log file'''
        try:
            log = open(self.tplogfname, "r").read()
        except RuntimeError:
            # Ok if log file isn't found, just given an message
            log = "log file missing"
        with h5py.File(self.fname, "a") as f:
            tplog_group = f["Logs/Tiepoint Logs"]
            dset = tplog_group.create_dataset(scene_name, data=log,
                                  dtype=h5py.special_dtype(vlen=bytes))

    def write_standard_metadata(self, m):
        # We copy the metadata, just changing the file we attach this to
        # and the local granule id
        with h5py.File(self.fname, "a") as f:
            mcopy = m.copy_new_file(f, self.local_granule_id)
            mcopy.write()
            
    def close(self):
        '''Finishing writing up data, and close file'''
        try:
            log = open(self.log_fname, "r").read()
        except RuntimeError:
            # Ok if log file isn't found, just given an message
            log = "log file missing"
        with h5py.File(self.fname, "a") as f:
            log_group = f["Logs"]
            dset = log_group.create_dataset("Overall Log", data=log,
                                dtype=h5py.special_dtype(vlen=bytes))

__all__ = ["L1bGeoQaFile"]
        
