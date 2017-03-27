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

BOOST_AUTO_TEST_CASE(image_coordinate)
{
  GeoCal::ImageCoordinate ic1(10,2000);
  GeoCal::ImageCoordinate ic2(10,10);
  GeoCal::ImageCoordinate ic3(250,100);
  boost::shared_ptr<GeoCal::GroundCoordinate> gp1 =
    igc->ground_coordinate(ic1);
  boost::shared_ptr<GeoCal::GroundCoordinate> gp2 =
    igc->ground_coordinate(ic2);
  boost::shared_ptr<GeoCal::GroundCoordinate> gp3 =
    igc->ground_coordinate(ic3);
  GeoCal::ImageCoordinate ic1_calc = igc->image_coordinate(*gp1);
  GeoCal::ImageCoordinate ic2_calc = igc->image_coordinate(*gp2);
  GeoCal::ImageCoordinate ic3_calc = igc->image_coordinate(*gp3);
  BOOST_CHECK_CLOSE(ic1_calc.line, ic1.line, 1e-1);
  BOOST_CHECK_CLOSE(ic1_calc.sample, ic1.sample, 1e-1);
  BOOST_CHECK_CLOSE(ic2_calc.line, ic2.line, 1e-1);
  BOOST_CHECK_CLOSE(ic2_calc.sample, ic2.sample, 1e-1);
  BOOST_CHECK_CLOSE(ic3_calc.line, ic3.line, 1e-1);
  BOOST_CHECK_CLOSE(ic3_calc.sample, ic3.sample, 1e-1);
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
