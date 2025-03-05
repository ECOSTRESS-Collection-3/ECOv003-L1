from .gaussian_stretch import *
import geocal
from test_support import *

#@skip
def test_gaussian_stretch(isolated_dir, rad_fname):
    b = 4
    ras = geocal.GdalRasterImage("HDF5:\"%s\"://Radiance/radiance_%d" %
                                 (rad_fname, b))
    d = gaussian_stretch(ras.read_all_double())
    f = geocal.VicarRasterImage("d_stretch.img", "BYTE", d.shape[0], d.shape[1])
    print(d.min())
    print(d.max())
    f.write(0,0,d)
    
    


