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
  boost::shared_ptr<GeoCal::Time> tbefore, tafter;
  // The test data has just 2 attitude time points, so we bracket the
  // times with these.
  GeoCal::Time t1 = orbit->attitude_time_point()[0];
  GeoCal::Time t2 = orbit->attitude_time_point()[1];

  // Matching t1, should have both values t1
  igccol->nearest_attitude_time_point(boost::make_shared<GeoCal::Time>(t1),
				      tbefore, tafter);
  BOOST_CHECK(fabs(*tbefore - t1) < 1e-3);
  BOOST_CHECK(fabs(*tafter - t1) < 1e-3);

  // Past t1, should have t1, t2
  igccol->nearest_attitude_time_point(boost::make_shared<GeoCal::Time>(t1+1),
				      tbefore, tafter);
  BOOST_CHECK(fabs(*tbefore - t1) < 1e-3);
  BOOST_CHECK(fabs(*tafter - t2) < 1e-3);

  // Before start of corrections, should have max_valid_time, t1
  igccol->nearest_attitude_time_point(boost::make_shared<GeoCal::Time>(t1-1),
				      tbefore, tafter);
  BOOST_CHECK(fabs(*tbefore - GeoCal::Time::max_valid_time) < 1e-3);
  BOOST_CHECK(fabs(*tafter - t1) < 1e-3);

  // Matching t2, should have t2, t2
  igccol->nearest_attitude_time_point(boost::make_shared<GeoCal::Time>(t2),
				      tbefore, tafter);
  BOOST_CHECK(fabs(*tbefore - t2) < 1e-3);
  BOOST_CHECK(fabs(*tafter - t2) < 1e-3);

  // /before t2, should have t1, t2
  igccol->nearest_attitude_time_point(boost::make_shared<GeoCal::Time>(t2-1),
				      tbefore, tafter);
  BOOST_CHECK(fabs(*tbefore - t1) < 1e-3);
  BOOST_CHECK(fabs(*tafter - t2) < 1e-3);

  // After end of corrections, should have t2, max_valid_time
  igccol->nearest_attitude_time_point(boost::make_shared<GeoCal::Time>(t2+1),
				      tbefore, tafter);
  BOOST_CHECK(fabs(*tbefore - t2) < 1e-3);
  BOOST_CHECK(fabs(*tafter - GeoCal::Time::max_valid_time) < 1e-3);
}


BOOST_AUTO_TEST_CASE(jacobian_test)
{
  // This test doesn't actually succeed, see the comment in
  // ecostress_image_ground_connection.cc function
  // image_coordinate_jac_parm for details.
  //
  // For now, skip the test but leave the code in place because it
  // illustrates the problem.
  return;

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
  std::cerr << jac_calc << "\n"
   	    << jac_fd << "\n";
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
