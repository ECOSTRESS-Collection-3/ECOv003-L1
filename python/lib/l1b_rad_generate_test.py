from .l1b_rad_generate import *
from .l1b_proj import *
from .l1a_pix_simulate import *
from geocal import write_shelve, Landsat7Global, VicarRasterImage, mmap_file
from test_support import *
from multiprocessing import Pool
import subprocess

@skip
def test_l1b_rad_generate(isolated_dir, igc_hres, dn_fname, gain_fname):
    l1brad = L1bRadGenerate(igc_hres, dn_fname, gain_fname,
                            "ECOSTRESS_L1B_RAD_80005_001_20150124T204251_0100_01.h5")
    l1brad.run()

# Don't normally run this. We had this in place to look at band to band
# registration, and this test looks at directly projecting each band to make
# sure the underlying data registers
@skip
def test_proj_band_to_band(igc_btob, test_data, ortho, aster_mosaic_surface_data):
    dn_fname = test_data + "band_to_band/ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_01.h5"
    pool = Pool(20)
    igccol = EcostressIgcCollection()
    igccol.add_igc(igc_btob)
    for i in range(6):
        igc_btob.band = i
        # Not sure why, but GdalRasterImage doesn't seem to be open correctly
        # when we spawn. Can worry about this at some point, but for now
        # just translate to VICAR
        subprocess.run(["gdal_translate", "-of", "VICAR", 'HDF5:"%s"://UncalibratedDN/b%d_image' % (dn_fname, i+1), "b_%d.img" % (i+1)])
        #igc_btob.image = GdalRasterImage('HDF5:"%s"://UncalibratedDN/b%d_image' % (dn_fname, i+1))
        igc_btob.image = VicarLiteRasterImage("b_%d.img" % (i+1))
        print("Doing band %d" % (i+1))
        p = L1bProj(igccol, ["proj_b%d.img" % (i+1)], ["ref_b%d.img" % (i+1)],
                    ortho)
        p.proj(pool=pool)
    # Check results with something like
    # vicarb "accck proj_b1.img proj_b2.img remap=n echo=no | grep MSG"

# Test to directly write out results of simulation. Not something we normally
# run, but we had this in place when we were investigating issues with the
# simulation (since fixed - problem was just that we were using the wrong
# camera model).
@skip        
def test_proj_dir_simulate(igc_hres, test_data, aster_mosaic_surface_data):
    pool = Pool(20)
    l1a_pix_sim = L1aPixSimulate(igc_hres, aster_mosaic_surface_data)
    data = l1a_pix_sim.image(0, pool=pool)
    f = VicarRasterImage("sim_0.img", "HALF", data.shape[0], data.shape[1])
    f.close()
    fdata = mmap_file("sim_0.img", mode="r+")
    fdata[:,:]  = data
    
