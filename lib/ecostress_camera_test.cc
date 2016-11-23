#include "geocal/unit_test_support.h"
#include "geocal/hdf_orbit.h"
#include "ecostress_camera.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_camera, GeoCal::GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressCamera cam;
  // We'll need to create fixture with this stuff
  std::string orb_fname = "/data/smyth/ecostress-test-data/latest/L1A_RAW_ATT_80005_20150124T204251_0100_01.h5.expected";
  orb =GeoCal::HdfOrbit<GeoCal::Eci, GeoCal::TimeJ2000Creator>
    (orb_fname, "", "Ephemeris/time_j2000", "Ephemeris/eci_position",
     "Ephemeris/eci_velocity", "Attitude/time_j2000", "Attitude/quaternion");
  GeoCal::Time t = GeoCal::Time::parse_time("2015-01-24T20:42:51.230216Z");
  boost::shared_ptr<GeoCal::OrbitData> od = orb.orbit_data(t);
  GeoCal::SimpleDem dem;
  boost::shared_ptr<GeoCal::CartesianFixed> gp1 =
    od->surface_intersect(cam, GeoCal::FrameCoordinate(0,0), dem);
  std::cerr << *gp1 << "\n";
}
