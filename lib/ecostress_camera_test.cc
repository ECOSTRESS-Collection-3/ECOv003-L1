// #include "geocal/unit_test_support.h"
#include <boost/test/unit_test.hpp>
#include <boost/test/floating_point_comparison.hpp>
#include "geocal/hdf_orbit.h"
#include "geocal/simple_dem.h"
#include "ecostress_camera.h"

// We'll move this, but for now place here
namespace Ecostress {
/****************************************************************//**
  This is a global fixture that is available to all unit tests.
*******************************************************************/
class GlobalFixture {
public:
  GlobalFixture() {}
  virtual ~GlobalFixture() { /* Nothing to do now */ }
};
}

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_camera, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressCamera cam;
  // We'll need to create fixture with this stuff
  std::string orb_fname = "/data/smyth/ecostress-test-data/latest/L1A_RAW_ATT_80005_20150124T204251_0100_01.h5.expected";
  GeoCal::HdfOrbit<GeoCal::Eci, GeoCal::TimeJ2000Creator> orb
    (orb_fname, "", "Ephemeris/time_j2000", "Ephemeris/eci_position",
     "Ephemeris/eci_velocity", "Attitude/time_j2000", "Attitude/quaternion");
  GeoCal::Time t = GeoCal::Time::parse_time("2015-01-24T20:42:52Z");
  boost::shared_ptr<GeoCal::OrbitData> od = orb.orbit_data(t);
  GeoCal::SimpleDem dem;
  boost::shared_ptr<GeoCal::CartesianFixed> gp1 =
    od->surface_intersect(cam, GeoCal::FrameCoordinate(0,0), dem);
  boost::shared_ptr<GeoCal::CartesianFixed> gp2 =
    od->surface_intersect(cam, GeoCal::FrameCoordinate(1,0), dem);
  boost::shared_ptr<GeoCal::CartesianFixed> gp3 =
    od->surface_intersect(cam, GeoCal::FrameCoordinate(0,1), dem);
  std::cerr << distance(*gp1, *gp2) << "\n";
  std::cerr << distance(*gp1, *gp3) << "\n";
}
BOOST_AUTO_TEST_SUITE_END()
