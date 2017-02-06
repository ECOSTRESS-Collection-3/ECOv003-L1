#include "unit_test_support.h"
#include "ground_coordinate_array.h"
#include "ecostress_igc_fixture.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ground_coordinate_array, EcostressIgcFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  GroundCoordinateArray gca(igc);
  blitz::Array<double, 3> res = gca.ground_coor_arr(0);
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
