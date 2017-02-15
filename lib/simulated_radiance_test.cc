#include "unit_test_support.h"
#include "simulated_radiance.h"
#include "ecostress_igc_fixture.h"
#include "geocal/srtm_dem.h"
#include "geocal/geodetic.h"
#include "geocal/vicar_lite_file.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(simulated_radiance, EcostressIgcFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  if(aster_mosaic_dir() == "") {
    BOOST_WARN_MESSAGE(false, "Skipping SimulatedRadiance test because ASTER mosaic data wasn't found");
    return;
  }
  SimulatedRadiance srad(boost::make_shared<GroundCoordinateArray>(igc),
			 boost::make_shared<GeoCal::VicarLiteRasterImage>(aster_mosaic_dir() + "calnorm_b4.img"));
  std::cerr << srad;
  // blitz::Array<double, 3> res = gca.ground_coor_scan_arr(4, 20);
  // BOOST_CHECK_EQUAL(res.rows(), 20);
  // BOOST_CHECK_EQUAL(res.cols(), 5400);
  // BOOST_CHECK_EQUAL(res.depth(), 3);
  // GeoCal::Geodetic pt(res(10-4,20,0),res(10-4,20,1),res(10-4,20,2));
  // BOOST_CHECK(distance(pt, *igc->ground_coordinate(GeoCal::ImageCoordinate(10, 20))) < 1.0);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  if(aster_mosaic_dir() == "") {
    BOOST_WARN_MESSAGE(false, "Skipping SimulatedRadiance test because ASTER mosaic data wasn't found");
    return;
  }
  boost::shared_ptr<SimulatedRadiance> srad =
    boost::make_shared<SimulatedRadiance>
    (boost::make_shared<GroundCoordinateArray>(igc),
     boost::make_shared<GeoCal::VicarLiteRasterImage>(aster_mosaic_dir() + "calnorm_b4.img"));
  std::string d = GeoCal::serialize_write_string(srad);
  if(false)
    std::cerr << d;
  boost::shared_ptr<SimulatedRadiance> sradr =
    GeoCal::serialize_read_string<SimulatedRadiance>(d);
}

BOOST_AUTO_TEST_SUITE_END()
