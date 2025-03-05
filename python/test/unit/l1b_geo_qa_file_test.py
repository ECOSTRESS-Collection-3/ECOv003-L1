from ecostress.l1b_geo_qa_file import L1bGeoQaFile


def test_l1b_geo_qa_file(isolated_dir):
    with open("test.log", "w") as fh:
        print("This is a fake log file", file=fh)
    f = L1bGeoQaFile("test_qa.h5", "test.log")
    # dname = "/home/smyth/Local/ecostress-build/build/l1b_geo_run/"
    # f.write_xml(dname + "igccol_initial.xml", dname + "tpcol.xml",
    #            dname + "igccol_sba.xml", dname + "tpcol_sba.xml")
    # orb = read_shelve(dname + "igccol_sba.xml").image_ground_connection(0).orbit
    # f.add_orbit(orb)
    f.close()
