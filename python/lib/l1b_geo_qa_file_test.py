from .l1b_geo_qa_file import *
from test_support import *

def test_l1b_geo_qa_file(isolated_dir):
    with open("test.log", "w") as fh:
        print("This is a fake log file", file=fh)
    f = L1bGeoQaFile("test_qa.h5", "test.log")
    #dname = "/home/smyth/Local/ecostress-build/build/l1b_geo_run/"
    #f.write_xml(dname + "igccol_initial.xml", dname + "tpcol.xml",
    #            dname + "igccol_sba.xml", dname + "tpcol_sba.xml")
    f.close()




