from ecostress import L1bGeoQaFile
import io
from pathlib import Path
import pytest


def test_l1b_geo_qa_file(isolated_dir):
    log_string_handle = io.StringIO()
    print("This is a fake log file", file=log_string_handle)
    f = L1bGeoQaFile("test_qa.h5", log_string_handle)
    # dname = "/home/smyth/Local/ecostress-build/build/l1b_geo_run/"
    # f.write_xml(dname + "igccol_initial.xml", dname + "tpcol.xml",
    #            dname + "igccol_sba.xml", dname + "tpcol_sba.xml")
    # orb = read_shelve(dname + "igccol_sba.xml").image_ground_connection(0).orbit
    # f.add_orbit(orb)
    f.close()


# We don't normally run this, since it depends on having run the end to end run
# plus having a hard coded path. But useful to keep this around in case we
# run into some sort of issue that we need to debug
@pytest.mark.skip
def test_read_l1b_geo_qa_file():
    bpath = Path("/home/smyth/Local/ecostress-build/build_conda")
    fname = bpath / "end_to_end_test_l1b_geo" / "L1B_GEO_QA_03663_20190227T101222_01.h5"
    print(L1bGeoQaFile.pass_list(fname))
    sm = L1bGeoQaFile.scan_mirror(fname, 1)
    print(sm)
    tt = L1bGeoQaFile.time_table(fname, 1)
    print(tt)
    tpcol = L1bGeoQaFile.tpcol(fname, pass_number=1)
    print(tpcol)
    scene_list = L1bGeoQaFile.scene_list(fname)
    print(scene_list)
    ofile = L1bGeoQaFile.orbit_filename(fname)
    print(ofile)
    l1bfname = L1bGeoQaFile.l1b_rad_list(fname)
    print(l1bfname)
    igccol = L1bGeoQaFile.igccol(fname)
    print(igccol)
    df = L1bGeoQaFile.data_frame(fname)
    print(df)

# Read collection 2 data    
@pytest.mark.skip
def test_read_collection2_l1b_geo_qa_file():
    bpath = Path("/arcdata/smyth/L1B_GEO_QA/2025/04/01")
    fname = bpath / "L1B_GEO_QA_38184_20250401T001052_0713_01.h5"
    # Not in collection 2
    with pytest.raises(RuntimeError, match="scan_mirror is not available in collection 2 l1b_geo_qa"):
        sm = L1bGeoQaFile.scan_mirror(fname, 1)
        print(sm)
    with pytest.raises(RuntimeError, match="time_table is not available in collection 2 l1b_geo_qa"):
        tt = L1bGeoQaFile.time_table(fname, 1)
        print(tt)
    tpcol = L1bGeoQaFile.tpcol(fname)
    print(tpcol)
    scene_list = L1bGeoQaFile.scene_list(fname)
    print(scene_list)
    ofile = L1bGeoQaFile.orbit_filename(fname)
    print(ofile)
    l1bfname = L1bGeoQaFile.l1b_rad_list(fname)
    print(l1bfname)
    with pytest.raises(RuntimeError, match="igccol is not available in collection 2 l1b_geo_qa"):
        igccol = L1bGeoQaFile.igccol(fname)
        print(igccol)
    df = L1bGeoQaFile.data_frame(fname)
    print(df)
