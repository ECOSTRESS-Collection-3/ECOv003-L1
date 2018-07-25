#include "unit_test_support.h"
#include "ecostress_scan_mirror.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_scan_mirror, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressScanMirror sm(-25.5, 25.5);
  BOOST_CHECK_CLOSE(sm.scan_mirror_angle(0, 0),
		    -25.5, 1e-2);
  BOOST_CHECK_CLOSE(sm.scan_mirror_angle(0, 20.3),
		    -25.5 + (25.5 + 25.5) / (5400-1) * 20.3, 1e-2);
}

BOOST_AUTO_TEST_CASE(fill_missing_test)
{
  EcostressScanMirror sm_original(-25.5, 25.5);
  blitz::Array<int, 2> ev_missing(sm_original.encoder_value().copy());
  // Test missing part of a line
  ev_missing(42, blitz::Range(0,1000)) = -1;
  ev_missing(43, blitz::Range(3000,5399)) = -1;
  EcostressScanMirror sm_missing_1(ev_missing);
  BOOST_CHECK_CLOSE(sm_missing_1.scan_mirror_angle(42, 0),
		    sm_original.scan_mirror_angle(42, 0), 1e-2);
  BOOST_CHECK_CLOSE(sm_missing_1.scan_mirror_angle(43, 5000),
		    sm_original.scan_mirror_angle(43, 5000), 1e-2);
  // Test missing a whole line
  ev_missing = sm_original.encoder_value();
  ev_missing(42, blitz::Range::all()) = -1;
  ev_missing(43, blitz::Range::all()) = -1;
  EcostressScanMirror sm_missing_2(ev_missing);
  BOOST_CHECK_CLOSE(sm_missing_2.scan_mirror_angle(42, 0),
		    sm_original.scan_mirror_angle(42, 0), 1e-2);
  BOOST_CHECK_CLOSE(sm_missing_2.scan_mirror_angle(43, 5000),
		    sm_original.scan_mirror_angle(43, 5000), 1e-2);
  // Test missing whole first lines
  ev_missing = sm_original.encoder_value();
  ev_missing(0, blitz::Range::all()) = -1;
  ev_missing(1, blitz::Range::all()) = -1;
  EcostressScanMirror sm_missing_3(ev_missing);
  BOOST_CHECK_CLOSE(sm_missing_3.scan_mirror_angle(0, 0),
		    sm_original.scan_mirror_angle(0, 0), 1e-2);
  BOOST_CHECK_CLOSE(sm_missing_3.scan_mirror_angle(1, 5000),
		    sm_original.scan_mirror_angle(1, 5000), 1e-2);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<EcostressScanMirror> sm =
    boost::make_shared<EcostressScanMirror>(-25.5,25.5);
  std::string d = GeoCal::serialize_write_string(sm);
  if(false)
    std::cerr << d;
  boost::shared_ptr<EcostressScanMirror> smr =
    GeoCal::serialize_read_string<EcostressScanMirror>(d);
  BOOST_CHECK_CLOSE(smr->scan_mirror_angle(0, 0),
		    -25.5, 1e-2);
  BOOST_CHECK_CLOSE(smr->scan_mirror_angle(0, 20.3),
		    -25.5 + (25.5 + 25.5) / (5400-1) * 20.3, 1e-2);
}

BOOST_AUTO_TEST_SUITE_END()
