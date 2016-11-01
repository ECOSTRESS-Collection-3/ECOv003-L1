from geocal import *
import h5py
import shutil
from .write_standard_metadata import WriteStandardMetadata
from .misc import ecostress_file_name

class L1aRawPixGenerate(object):
    '''This generates a L1A_RAW_PIX, L1A_BB, L1A_ENG and L1A_RAW_ATT
    files from a L0 input.'''
    def __init__(self, l0, run_config = None, build_id = "0.20",
                 pge_version = "0.20", build_version="0100",
                 file_version = "01"):
        '''Create a L1aRawPixGenerate to process the given L0 file. 
        To actually generate, execute the 'run' command.'''
        self.l0 = l0
        self.run_config = run_config
        self.build_id = build_id
        self.pge_version = pge_version
        self.build_version = build_version
        self.file_version = file_version

    def hdf_copy(self, fname, group, group_in = None, scene = None):
        '''Copy the given group from out input to the given file.
        Default it to give the input the same group name, but can change this. If
        scene is passed in, we nest the output by "Scene_<num>"'''
        if(group_in is None):
            if(scene is not None):
                group_in = "/Data/Scene_%d%s" % (scene, group)
            else:
                group_in = "/Data" + group
        subprocess.run(["h5copy", "-i", self.l0, "-o", fname, "-p",
                        "-s", group_in,
                        "-d", group], check=True)

    def create_file(self, prod_type, orbit, scene, primary_file = False):
        '''Create the file, generate the standard metadata, and return
        the file name.'''
        if(scene is None):
            basegroup = "/Data"
        else:
            basegroup = "/Data/Scene_%d" % scene
            
        bdate = self.fin[basegroup + "/StandardMetadata/RangeBeginningDate"].value
        btime = self.fin[basegroup + "/StandardMetadata/RangeBeginningTime"].value
        edate = self.fin[basegroup + "/StandardMetadata/RangeEndingDate"].value
        etime = self.fin[basegroup + "/StandardMetadata/RangeEndingTime"].value
        bdtime = Time.parse_time("%sT%sZ" % (bdate, btime))
        fname = ecostress_file_name(prod_type, orbit, scene, bdtime,
                                    build=self.build_version,
                                    version=self.file_version)
        if(primary_file):
            self.log_fname =  os.path.splitext(fname)[0] + ".log"
            self.log = open(self.log_fname, "w")
        fout = h5py.File(fname, "w")
        m = WriteStandardMetadata(fout,
                                  product_specfic_group = prod_type + "Metadata",
                                  pge_name="L1A_RAW_PIX",
                                  build_id = self.build_id,
                                  pge_version=self.pge_version,
                                  orbit_based = (scene is None))
        if(self.run_config is not None):
            m.process_run_config_metadata(self.run_config)
        m.set("RangeBeginningDate", bdate)
        m.set("RangeBeginningTime", btime)
        m.set("RangeEndingDate", edate)
        m.set("RangeEndingTime", etime)
        m.write()
        fout.close()
        return fname
        
    def run(self):
        '''Do the actual generation of data.'''
        self.log = None
        try:
            self.fin = h5py.File(self.l0,"r")
            onum = int(self.fin["/Data/StandardMetadata/StartOrbitNumber"].value)

            feng = self.create_file("L1A_ENG", onum, None, primary_file = True)
            fatt = self.create_file("L1A_RAW_ATT", onum, None)
            self.hdf_copy(feng, "/rtdBlackbodyGradients")
            self.hdf_copy(fatt, "/Attitude")
            self.hdf_copy(fatt, "/Ephemeris")

            # This cryptic expression gets a list of all the scenes by looking
            # for groups with the name "/Data/Scene_<number>"
            slist = [int(k.split('_')[1]) for k in self.fin["Data"].keys()
                     if re.match(r'Scene_\d+', k)]
            for scene in slist:
                fbb = self.create_file("L1A_BB", onum, scene)
                fpix = self.create_file("L1A_RAW_PIX", onum, scene)
                self.hdf_copy(fbb, "/BlackBodyPixels", scene=scene)
                self.hdf_copy(fpix, "/UncalibratedPixels", scene=scene)
                self.hdf_copy(fpix, "/Time", scene=scene)
            # Write out a dummy log file
            print("This is a dummy log file", file = self.log)
            print("L1A_RAW_PGE:ERROR-0-[Job Successful]", file=self.log)
            self.log.flush()
        except:
            if(self.log):
                print("L1A_RAW_PGE:ERROR-2-[Unexpected Error]", file=log)
                log.flush()
                raise
                
