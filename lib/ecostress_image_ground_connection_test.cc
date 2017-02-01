#include "unit_test_support.h"
#include "ecostress_image_ground_connection.h"
#include "ecostress_igc_fixture.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_image_ground_connection, EcostressIgcFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  BOOST_CHECK_EQUAL(igc->number_line(), 5632);
  BOOST_CHECK_EQUAL(igc->number_sample(), 5400);
  BOOST_CHECK_EQUAL(igc->number_band(), 6);
  BOOST_CHECK_CLOSE(igc->resolution(), 30.0, 1e-4);
  BOOST_CHECK_CLOSE(igc->max_height(), 9000.0, 1e-4);
  BOOST_CHECK_EQUAL(igc->band(),
		    (int) EcostressImageGroundConnection::REF_BAND);
  BOOST_CHECK(distance(*igc->ground_coordinate(GeoCal::ImageCoordinate(10,10)),
		       GeoCal::Geodetic(37.7166702741, -124.572923589)) < 1.0);
}


BOOST_AUTO_TEST_CASE(serialization)
{
  std::string d = GeoCal::serialize_write_string(igc);
  if(false)
    std::cerr << d;
  boost::shared_ptr<EcostressImageGroundConnection> igcr =
    GeoCal::serialize_read_string<EcostressImageGroundConnection>(d);
  BOOST_CHECK(distance(*igc->ground_coordinate(GeoCal::ImageCoordinate(10,10)),
		       GeoCal::Geodetic(37.7166702741, -124.572923589)) < 1.0);
}

BOOST_AUTO_TEST_SUITE_END()
