#include "unit_test_support.h"
#include "ecostress_scan_mirror.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_scan_mirror, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressScanMirror sm;
  BOOST_CHECK_CLOSE(sm.scan_start(), -25.5, 1e-4);
  BOOST_CHECK_CLOSE(sm.scan_end(), 25.5, 1e-4);
  BOOST_CHECK_EQUAL(sm.number_sample(), 5400);
  BOOST_CHECK_CLOSE(sm.scan_mirror_angle(0, 0),
		    -25.5, 1e-4);
  BOOST_CHECK_CLOSE(sm.scan_mirror_angle(0, 20.3),
		    -25.5 + (25.5 + 25.5) / 5400 * 20.3, 1e-4);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<EcostressScanMirror> sm =
    boost::make_shared<EcostressScanMirror>();
  std::string d = GeoCal::serialize_write_string(sm);
  if(false)
    std::cerr << d;
  boost::shared_ptr<EcostressScanMirror> smr =
    GeoCal::serialize_read_string<EcostressScanMirror>(d);
  BOOST_CHECK_CLOSE(smr->scan_start(), -25.5, 1e-4);
  BOOST_CHECK_CLOSE(smr->scan_end(), 25.5, 1e-4);
  BOOST_CHECK_EQUAL(smr->number_sample(), 5400);
  BOOST_CHECK_CLOSE(smr->scan_mirror_angle(0, 0),
		    -25.5, 1e-4);
  BOOST_CHECK_CLOSE(smr->scan_mirror_angle(0, 20.3),
		    -25.5 + (25.5 + 25.5) / 5400 * 20.3, 1e-4);
}

BOOST_AUTO_TEST_SUITE_END()
