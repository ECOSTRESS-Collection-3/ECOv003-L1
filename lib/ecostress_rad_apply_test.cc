#include "unit_test_support.h"
#include "ecostress_rad_apply.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_rad_apply, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  std::string dn_name = test_data_dir() + "ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_02.h5.expected";
  std::string gain_name = test_data_dir() + "L1A_RAD_GAIN_80005_001_20150124T204250_0100_02.h5.expected";
  EcostressRadApply r(dn_name, gain_name, 1);
  BOOST_CHECK_CLOSE(r.read_double(200,2000,1,1)(0,0), 6.3079550273250788, 1e-2);
  EcostressRadApply r2(dn_name, gain_name, 0);
  BOOST_CHECK_CLOSE(r2.read_double(200,2000,1,1)(0,0), 46, 1e-2);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  std::string dn_name = test_data_dir() + "ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_02.h5.expected";
  std::string gain_name = test_data_dir() + "L1A_RAD_GAIN_80005_001_20150124T204250_0100_02.h5.expected";
  boost::shared_ptr<EcostressRadApply> r =
    boost::make_shared<EcostressRadApply>(dn_name, gain_name, 1);
  std::string d = GeoCal::serialize_write_string(r);
  if(false)
    std::cerr << d;
  boost::shared_ptr<EcostressRadApply> rr =
    GeoCal::serialize_read_string<EcostressRadApply>(d);
  BOOST_CHECK_CLOSE(rr->read_double(200,2000,1,1)(0,0),
		    r->read_double(200,2000,1,1)(0,0), 1e-2);
}

BOOST_AUTO_TEST_SUITE_END()
