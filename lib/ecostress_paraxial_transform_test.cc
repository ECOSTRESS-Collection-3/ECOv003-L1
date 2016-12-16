#include "unit_test_support.h"
#include "ecostress_paraxial_transform.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_paraxial_transform, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  boost::shared_ptr<EcostressParaxialTransform> tran =
    GeoCal::serialize_read<EcostressParaxialTransform>(unit_test_data_dir() + "cam_paraxial.xml");
  // Point read directly from spreadsheet we generated data from.
  double par_x_expect = 5.11982;
  double par_y_expect = 5.12022;
  double real_x_expect = 5.04128;
  double real_y_expect = 4.937;
  double real_x, real_y, par_x, par_y;
  tran->paraxial_to_real(par_x_expect, par_y_expect, real_x, real_y);
  BOOST_CHECK_CLOSE(real_x, real_x_expect, 1e-1);
  BOOST_CHECK_CLOSE(real_y, real_y_expect, 1e-1);
  tran->real_to_paraxial(real_x_expect, real_y_expect, par_x, par_y);
  BOOST_CHECK_CLOSE(par_x, par_x_expect, 1e-1);
  BOOST_CHECK_CLOSE(par_y, par_y_expect, 1e-1);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<EcostressParaxialTransform> tran(new EcostressParaxialTransform());
  for(int i = 0; i < tran->par_to_real().rows(); ++i)
    for(int j = 0; j < tran->par_to_real().cols(); ++j) {
      tran->par_to_real()(i,j) = i + j;
      tran->real_to_par()(i,j) = i + j;
    }
  std::string d = GeoCal::serialize_write_string(tran);
  if(false)
    std::cerr << d;
  boost::shared_ptr<EcostressParaxialTransform> tranr =
    GeoCal::serialize_read_string<EcostressParaxialTransform>(d);
  BOOST_CHECK_MATRIX_CLOSE(tran->par_to_real(), tranr->par_to_real());
  BOOST_CHECK_MATRIX_CLOSE(tran->real_to_par(), tranr->real_to_par());
}

BOOST_AUTO_TEST_SUITE_END()
