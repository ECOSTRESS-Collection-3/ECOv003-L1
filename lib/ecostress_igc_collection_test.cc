#include "unit_test_support.h"
#include "ecostress_igc_collection.h"
#include "ecostress_igc_fixture.h"
#include "geocal/igc_array.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_igc_collection, EcostressIgcFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  boost::shared_ptr<EcostressIgcCollection> igccol = boost::make_shared<EcostressIgcCollection>();
  igccol->add_igc(igc);
  BOOST_CHECK_EQUAL(igccol->number_image(), 1);
}


BOOST_AUTO_TEST_CASE(jacobian_test)
{
  boost::shared_ptr<EcostressIgcCollection> igccol = boost::make_shared<EcostressIgcCollection>();
  igccol->add_igc(igc);
  GeoCal::ImageCoordinate ic(10,2000);
  boost::shared_ptr<GeoCal::GroundCoordinate> gp =
    igccol->ground_coordinate(0, ic);
  igccol->add_identity_gradient();
  blitz::Array<double, 1> pstep(12);
  pstep = 1,1,1,1,1,1,1,1,1,1,1,1;
  blitz::Array<double, 2> jac_calc =
    igccol->image_coordinate_jac_parm(0, *gp->convert_to_cf());
  blitz::Array<double, 2> jac_fd =
    igccol->image_coordinate_jac_parm_fd(0, *gp->convert_to_cf(), pstep);
  // std::cerr << jac_calc << "\n"
  // 	    << jac_fd << "\n";
  BOOST_CHECK_MATRIX_CLOSE_TOL(jac_calc, jac_fd, 1e-4);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<EcostressIgcCollection> igccol = boost::make_shared<EcostressIgcCollection>();
  igccol->add_igc(igc);
  std::string d = GeoCal::serialize_write_string(igccol);
  if(false)
    std::cerr << d;
  boost::shared_ptr<EcostressIgcCollection> igccolr =
    GeoCal::serialize_read_string<EcostressIgcCollection>(d);
  BOOST_CHECK_EQUAL(igccolr->number_image(), 1);
}

BOOST_AUTO_TEST_SUITE_END()
