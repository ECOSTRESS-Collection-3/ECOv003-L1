#include "unit_test_support.h"
#include "ecostress_orbit.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_orbit, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressOrbit orb(unit_test_data_dir() + "L1A_RAW_ATT_00049_20180709T214305_0400_01.h5");
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<EcostressOrbit> orb =
    boost::make_shared<EcostressOrbit>(unit_test_data_dir() + "L1A_RAW_ATT_00049_20180709T214305_0400_01.h5");
  std::string d = GeoCal::serialize_write_string(orb);
  if(false)
    std::cerr << d;
  boost::shared_ptr<GeoCal::Orbit> orbr =
    GeoCal::serialize_read_string<GeoCal::Orbit>(d);
  BOOST_CHECK_CLOSE(orb->min_time().pgs(), orbr->min_time().pgs(), 1e-4);
  BOOST_CHECK_CLOSE(orb->max_time().pgs(), orbr->max_time().pgs(), 1e-4);
}

BOOST_AUTO_TEST_SUITE_END()
