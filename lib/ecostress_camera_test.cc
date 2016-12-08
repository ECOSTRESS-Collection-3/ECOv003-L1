#include "unit_test_support.h"
#include "geocal/hdf_orbit.h"
#include "geocal/simple_dem.h"
#include "ecostress_camera.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_camera, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressCamera cam;
  // We'll need to create fixture with this stuff
  std::string orb_fname = test_data_dir() +
    "L1A_RAW_ATT_80005_20150124T204251_0100_01.h5.expected";
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

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<GeoCal::Camera> cam(new EcostressCamera());
  std::string d = GeoCal::serialize_write_string(cam);
  if(false)
    std::cerr << d;
  boost::shared_ptr<GeoCal::Camera> camr =
    GeoCal::serialize_read_string<GeoCal::Camera>(d);
  BOOST_CHECK_EQUAL(cam->number_band(), camr->number_band());
}

BOOST_AUTO_TEST_SUITE_END()
