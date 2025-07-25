import geocal
from ecostress import EcostressCamera

focal_length = 427.5
frame_to_sc_q = geocal.Quaternion_double(0, 0, 0, 1)


def test_basic():
    """Make sure we can create a camera, and print it out."""
    cam = EcostressCamera(focal_length, 1.0, 0, frame_to_sc_q)
    print(cam)


def test_camera_use(igc_old, unit_test_data):
    """Basic test of have camera used by geocal."""
    ic = geocal.ImageCoordinate(0, 0)
    t, fc = igc_old.ipi.time_table.time(ic)
    od = igc_old.ipi.orbit.orbit_data(t)
    dem = igc_old.dem
    cam = geocal.read_shelve(str(unit_test_data / "camera.xml"))
    gp1 = od.surface_intersect(cam, fc, dem)
    fc.line = fc.line + 1
    gp2 = od.surface_intersect(cam, fc, dem)
    fc.line = fc.line - 1
    fc.sample = fc.sample + 1
    gp3 = od.surface_intersect(cam, fc, dem)
    print(geocal.distance(gp1, gp2))
    print(geocal.distance(gp1, gp3))


def test_serialize(isolated_dir):
    cam = EcostressCamera(focal_length, 1.0, 0, frame_to_sc_q)
    geocal.write_shelve("cam.xml", cam)
    cam2 = geocal.read_shelve("cam.xml")
    print(cam2)
