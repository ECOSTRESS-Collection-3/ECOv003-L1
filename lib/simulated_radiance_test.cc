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
  // Normally we want to average the ASTER data, but to speed up this
  // unit test skip this step.
  int avg_fact = 1;
  SimulatedRadiance srad(boost::make_shared<GroundCoordinateArray>(igc),
			 boost::make_shared<GeoCal::VicarLiteRasterImage>(aster_mosaic_dir() + "calnorm_b4.img", 1, GeoCal::VicarLiteFile::READ, 1000, 1000),
			 avg_fact);
  blitz::Array<double, 2> res = srad.radiance_scan(4, 20);
  BOOST_CHECK_EQUAL(res.rows(), 20);
  BOOST_CHECK_EQUAL(res.cols(), 5400);
  BOOST_CHECK_CLOSE(res(0,5000), 64.60212, 2e-2);
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
