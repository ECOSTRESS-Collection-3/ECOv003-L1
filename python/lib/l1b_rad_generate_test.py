from .l1b_rad_generate import *
from .l1b_proj import *
from geocal import write_shelve, Landsat7Global
from test_support import *
from multiprocessing import Pool

@skip
def test_l1b_rad_generate(isolated_dir, igc_hres, dn_fname, gain_fname):
    l1brad = L1bRadGenerate(igc_hres, dn_fname, gain_fname,
                            "ECOSTRESS_L1B_RAD_80005_001_20150124T204251_0100_01.h5")
    l1brad.run()

@skip
def test_band_diff(igc_hres):
    write_shelve("igc.xml", igc_hres)


def test_proj_band_to_band(igc_btob, test_data):
    dn_fname = test_data + "band_to_band/ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_01.h5"
    pool = Pool(10)
    igccol = EcostressIgcCollection()
    igccol.add_igc(igc_btob)
    ortho = Landsat7Global("/project/ancillary/LANDSAT/band62_VICAR",
                           Landsat7Global.BAND62)
    for i in range(6):
        igc_btob.band = i
        igc_btob.image = GdalRasterImage('HDF5:"%s"://UncalibratedDN/b%d_image' % (dn_fname, i+1))
        print("Doing band %d" % (i+1))
        p = L1bProj(igccol, ["proj_b%d.img" % (i+1)], ["ref_b%d.img" % (i+1)],
                    ortho)
        p.proj(pool=pool)
