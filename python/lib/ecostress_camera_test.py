try:
    from ecostress_swig import *
except ImportError:
    raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
from geocal import *
from test_support import *

def test_basic():
    '''Make sure we can create a camera, and print it out.'''
    cam = EcostressCamera()
    print(cam)

def test_camera_use(igc, unit_test_data):
    '''Basic test of have camera used by geocal.'''
    ic = ImageCoordinate(0,0)
    t, fc = igc.ipi.time_table.time(ic)
    od = igc.ipi.orbit.orbit_data(t)
    dem = igc.dem
    cam = read_shelve(unit_test_data + "camera.xml")
    gp1 = od.surface_intersect(cam, fc, dem)
    fc.line = fc.line + 1
    gp2 = od.surface_intersect(cam, fc, dem)
    fc.line = fc.line - 1
    fc.sample = fc.sample + 1
    gp3 = od.surface_intersect(cam, fc, dem)
    print(distance(gp1, gp2))
    print(distance(gp1, gp3))    

def test_serialize(isolated_dir):
    cam = EcostressCamera()
    write_shelve("cam.xml", cam)
    cam2 = read_shelve("cam.xml")
    print(cam2)
    
    
