import h5py
import os
import gzip
import numpy as np
import subprocess

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

    def write_xml(self, igc_initial, tpcol, igc_sba, tpcol_sba):
        '''Write the xml serialization files. Note because these are large 
        we compress them. HDF5 does compression, but not apparently on 
        strings. You can access them, but need to manually decompress.
        Note also the serialization has hardcoded paths in them, so often
        you can't use this directly. But writing out as a file to examine
        can be useful.

        Also, we could just directly use the binary serialization. But I'm
        guessing that the xml is more portable. In any case, the compressed
        xml is about the same size as the binary serialization.

        To directly create the serialized objects, do something like:

        import ecostress
        import geocal
        import h5py
        import gzip
        t = h5py.File("test_qa.h5", "r")["PythonObject/igccol_initial"][()]
        igccol_initial = geocal.serialize_read_generic_string(gzip.decompress(t).decode('utf8'))
        '''
        with h5py.File(self.fname, "a") as f:
            data = []
            desc = []
            for inf in (igc_initial, tpcol, igc_sba, tpcol_sba):
                try:
                    data.append(open(inf,"r").read().encode('utf8'))
                except RuntimeError:
                    data.append(b"")
                try:
                    desc.append(subprocess.run(["shelve_show", inf],
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
                except RuntimeError:
                    desc.append(b"")
            g = f.create_group("PythonObject")
            # Note, we compress the data ourselves. While HDF5 supports
            # compression, it doesn't seem to do this with strings.
            for i,fout in enumerate(["igccol_initial", "tpcol",
                                     "igccol_sba", "tpcol_sba"]):
                dset = g.create_dataset(fout,
                                        data=np.void(gzip.compress(data[i])))
                dset = g.create_dataset(fout + "_desc", data=desc[i],
                                        dtype=h5py.special_dtype(vlen=bytes))

    def input_list(self, inlist):
        with h5py.File(self.fname, "a") as f:
            f.create_dataset("Input File List",
                             data=[i.encode('utf8') for i in inlist],
                             dtype=h5py.special_dtype(vlen=bytes))
            
    def add_tp_log(self, scene_name, tplogfname):
        '''Add a TP log file'''
        try:
            log = open(tplogfname, "r").read()
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
        
