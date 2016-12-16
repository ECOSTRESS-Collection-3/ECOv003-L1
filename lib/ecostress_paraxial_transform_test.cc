#include "unit_test_support.h"
#include "ecostress_paraxial_transform.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_paraxial_transform, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressParaxialTransform t;
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<EcostressParaxialTransform> tran(new EcostressParaxialTransform());
  for(int i = 0; i < tran->paraxial_to_real().rows(); ++i)
    for(int j = 0; j < tran->paraxial_to_real().cols(); ++j) {
      tran->paraxial_to_real()(i,j) = i + j;
      tran->real_to_paraxial()(i,j) = i + j;
    }
  std::string d = GeoCal::serialize_write_string(tran);
  if(false)
    std::cerr << d;
  boost::shared_ptr<EcostressParaxialTransform> tranr =
    GeoCal::serialize_read_string<EcostressParaxialTransform>(d);
  BOOST_CHECK_MATRIX_CLOSE(tran->paraxial_to_real(), tranr->paraxial_to_real());
}

BOOST_AUTO_TEST_SUITE_END()
