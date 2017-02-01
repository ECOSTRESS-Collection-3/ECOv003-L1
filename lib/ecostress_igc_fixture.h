#ifndef ECOSTRESS_IGC_FIXTURE_H
#define ECOSTRESS_IGC_FIXTURE_H
#include "global_fixture.h"
#include "ecostress_image_ground_connection.h"
#include "geocal/hdf_orbit.h"
#include "geocal/simple_dem.h"
#include "ecostress_camera.h"
#include "ecostress_scan_mirror.h"
#include "ecostress_time_table.h"
#include <boost/make_shared.hpp>

using namespace Ecostress;

namespace Ecostress {
/****************************************************************//**
  This is a test fixture that sets up a EcostressImageGroundConnection
  for use in testing.
*******************************************************************/

class EcostressIgcFixture: public GlobalFixture {
public:
  EcostressIgcFixture()
  {
    camera = GeoCal::serialize_read<EcostressCamera>
      (unit_test_data_dir() + "camera.xml");
    std::string orb_fname = test_data_dir() +
    "L1A_RAW_ATT_80005_20150124T204251_0100_01.h5.expected";
    orbit = boost::make_shared<GeoCal::HdfOrbit<GeoCal::Eci,
						GeoCal::TimeJ2000Creator> >
      (orb_fname, "", "Ephemeris/time_j2000", "Ephemeris/eci_position",
       "Ephemeris/eci_velocity", "Attitude/time_j2000", "Attitude/quaternion");
    GeoCal::Time tstart = GeoCal::Time::parse_time("2015-01-24T20:42:52Z");
    time_table = boost::make_shared<EcostressTimeTable>(tstart);
    dem = boost::make_shared<GeoCal::SimpleDem>();
    scan_mirror = boost::make_shared<EcostressScanMirror>();
    boost::shared_ptr<GeoCal::RasterImage> no_img;
    igc = boost::make_shared<EcostressImageGroundConnection>
      (orbit, time_table, camera, scan_mirror, dem, no_img, "Test title");
  }
  boost::shared_ptr<GeoCal::Dem> dem;
  boost::shared_ptr<EcostressCamera> camera;
  boost::shared_ptr<GeoCal::Orbit> orbit;
  boost::shared_ptr<GeoCal::TimeTable> time_table;
  boost::shared_ptr<EcostressScanMirror> scan_mirror;
  boost::shared_ptr<EcostressImageGroundConnection> igc;
};
}
#endif
