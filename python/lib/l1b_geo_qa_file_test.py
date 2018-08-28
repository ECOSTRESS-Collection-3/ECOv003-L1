from .l1b_geo_qa_file import *
from test_support import *

def test_l1b_geo_qa_file(isolated_dir):
    with open("test.log", "w") as fh:
        print("This is a fake log file", file=fh)
    f = L1bGeoQaFile("test_qa.h5", "test.log")
    f.close()




