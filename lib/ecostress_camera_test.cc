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
  BOOST_CHECK_CLOSE(distance(*gp1, *gp2), 38.89, 1e-2);
  BOOST_CHECK_CLOSE(distance(*gp1, *gp3), 38.89, 1e-2);
}

BOOST_AUTO_TEST_CASE(compare_spreadsheet)
{
  /// \TODO We are assuming center of pixel. Is that correct?
  // We get our current camera model from
  // https://bravo-lib.jpl.nasa.gov/docushare/dsweb/Get/Document-1882647/FPA%20distortion20140522.xlsx.
  // To test things, directly compare what we calculate with what
  // values we have from the spreadsheet.
  //
  // We have:
  //   Pixel line 0 has X of 5.12 mm, 256 is 5.12 mm (Note 256 is
  //   actually one past the max pixel)
  // For y, we have:
  //     Y values  pixel    Band  Index (1 based)
  //     3.20mm  -80 pixel  1.62  6  1.4  2
  //     1.92mm  -48        12.05 1  0.5  3
  //     0.64mm  -16        8.28  5  0.1  4
  //    -0.64mm   16        8.64  4  0.1  5
  //    -1.92mm   48        11.35 2  0.6  6
  //    -3.20mm   80        9.07  3  1.6  7
  EcostressCamera cam;
  blitz::Array<double, 1> yp_expect(6);
  yp_expect = 1.92, -1.92, -3.20, -0.64, 0.64, 3.20;
  for(int b = 0; b < yp_expect.rows(); ++b) {
    double xp, yp;
    cam.fc_to_focal_plane(GeoCal::FrameCoordinate(0,0), b, xp, yp);
    BOOST_CHECK_CLOSE(xp, 5.12, 1e-4);
    BOOST_CHECK_CLOSE(yp, yp_expect(b), 1e-4);
    cam.fc_to_focal_plane(GeoCal::FrameCoordinate(256,0), b, xp, yp);
    BOOST_CHECK_CLOSE(xp, -5.12, 1e-4);
    BOOST_CHECK_CLOSE(yp, yp_expect(b), 1e-4);
  }
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
