#include "unit_test_support.h"
#include "ecostress_image_ground_connection.h"
#include "geocal/hdf_orbit.h"
#include "geocal/simple_dem.h"
#include "ecostress_camera.h"
#include "ecostress_scan_mirror.h"
#include "ecostress_time_table.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_image_ground_connection, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  boost::shared_ptr<EcostressCamera> cam =
    GeoCal::serialize_read<EcostressCamera>(unit_test_data_dir() + "camera.xml");
  // We'll need to create fixture with this stuff
  std::string orb_fname = test_data_dir() +
    "L1A_RAW_ATT_80005_20150124T204251_0100_01.h5.expected";
  boost::shared_ptr<GeoCal::Orbit> orb
    (new GeoCal::HdfOrbit<GeoCal::Eci, GeoCal::TimeJ2000Creator>
     (orb_fname, "", "Ephemeris/time_j2000", "Ephemeris/eci_position",
      "Ephemeris/eci_velocity", "Attitude/time_j2000", "Attitude/quaternion"));
  GeoCal::Time tstart = GeoCal::Time::parse_time("2015-01-24T20:42:52Z");
  boost::shared_ptr<GeoCal::TimeTable> tt(new EcostressTimeTable(tstart));
  boost::shared_ptr<GeoCal::Dem> dem(new GeoCal::SimpleDem);
  boost::shared_ptr<EcostressScanMirror> sm(new EcostressScanMirror);
  boost::shared_ptr<GeoCal::RasterImage> no_img;
  EcostressImageGroundConnection igc(orb, tt, cam, sm, dem, no_img,
				     "Test title");
}


BOOST_AUTO_TEST_CASE(serialization)
{
  // std::string d = GeoCal::serialize_write_string(cam);
  // if(false)
  //   std::cerr << d;
  // boost::shared_ptr<GeoCal::Camera> camr =
  //   GeoCal::serialize_read_string<GeoCal::Camera>(d);
  // BOOST_CHECK_EQUAL(cam->number_band(), camr->number_band());
}

BOOST_AUTO_TEST_SUITE_END()
