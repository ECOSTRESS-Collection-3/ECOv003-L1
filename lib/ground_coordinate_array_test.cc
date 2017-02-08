#include "unit_test_support.h"
#include "ground_coordinate_array.h"
#include "ecostress_igc_fixture.h"
#include "geocal/srtm_dem.h"
#include "geocal/ecr.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ground_coordinate_array, EcostressIgcFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  GroundCoordinateArray gca(igc);
  blitz::Array<double, 3> res = gca.ground_coor_arr(4, 20);
  BOOST_CHECK_EQUAL(res.rows(), 20);
  BOOST_CHECK_EQUAL(res.cols(), 5400);
  BOOST_CHECK_EQUAL(res.depth(), 3);
  GeoCal::Ecr pt(res(10-4,20,0),res(10-4,20,1),res(10-4,20,2));
  BOOST_CHECK(distance(pt, *igc->ground_coordinate(GeoCal::ImageCoordinate(10, 20))) < 1.0);
}


BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<GroundCoordinateArray> gca =
    boost::make_shared<GroundCoordinateArray>(igc);
  std::string d = GeoCal::serialize_write_string(gca);
  if(false)
    std::cerr << d;
  boost::shared_ptr<GroundCoordinateArray> igcr =
    GeoCal::serialize_read_string<GroundCoordinateArray>(d);
}

BOOST_AUTO_TEST_SUITE_END()
