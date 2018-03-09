#include "unit_test_support.h"
#include "ecostress_time_table.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_time_table, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  GeoCal::Time tstart = GeoCal::Time::parse_time("2015-01-24T20:42:52Z");
  EcostressTimeTable tt(tstart);
  BOOST_CHECK_EQUAL(tt.averaging_done(), true);
  BOOST_CHECK(fabs(tt.min_time() - tstart) < 1e-6);
  BOOST_CHECK(fabs(tt.max_time() -
   (tstart + 44 * EcostressTimeTable::nominal_scan_spacing)) < 1e-6);
  BOOST_CHECK_EQUAL(tt.min_line(), 0);
  BOOST_CHECK_EQUAL(tt.max_line(), 44 * tt.number_line_scan() - 1);
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc;
  tt.time(GeoCal::ImageCoordinate(0, 0), t, fc);
  BOOST_CHECK(fabs(t - tstart) < 1e-6);
  BOOST_CHECK_CLOSE(fc.line, 0, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  tt.time(GeoCal::ImageCoordinate(127, 0), t, fc);
  BOOST_CHECK(fabs(t - tstart) < 1e-6);
  BOOST_CHECK_CLOSE(fc.line, 127 * 2, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  tt.time(GeoCal::ImageCoordinate(0, 20.4), t, fc);
  BOOST_CHECK(fabs(t -
		   (tstart + 20.4 * EcostressTimeTable::frame_time)) < 1e-6);
  BOOST_CHECK_CLOSE(fc.line, 0, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  tt.time(GeoCal::ImageCoordinate(127.4, 0), t, fc);
  BOOST_CHECK(fabs(t - tstart) < 1e-6);
  BOOST_CHECK_CLOSE(fc.line, 127.4 * 2, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  tt.time(GeoCal::ImageCoordinate(128.6, 0), t, fc);
  BOOST_CHECK(fabs(t -
     (tstart + 1 * EcostressTimeTable::nominal_scan_spacing) < 1e-6));
  BOOST_CHECK_CLOSE(fc.line, (128.6 - 1 * tt.number_line_scan()) * 2, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  for(int i = 0; i <= tt.max_line(); i+=10)
    for(double j = 0; j < 5400; j += 10.1) {
      GeoCal::ImageCoordinate ic(i, j);
      tt.time(ic, t, fc);
      GeoCal::ImageCoordinate ic2 = tt.image_coordinate(t, fc);
      // std::cerr << "-----------------------------\n";
      // std::cerr << ic << "\n" << t << "\n" << fc << "\n" << ic2 << "\n";
      // std::cerr << "-----------------------------\n";
      BOOST_CHECK_CLOSE(ic.line, ic2.line, 1e-4);
      BOOST_CHECK(fabs(ic.sample - ic2.sample) < 0.01);
    }
  BOOST_CHECK_EQUAL(tt.number_scan(), 44);
  int lstart, lend;
  tt.scan_index_to_line(3, lstart, lend);
  BOOST_CHECK_EQUAL(lstart, 128 * 3);
  BOOST_CHECK_EQUAL(lend, 128 * 4);
}

BOOST_AUTO_TEST_CASE(time_jac_test)
{
  GeoCal::Time tstart = GeoCal::Time::parse_time("2015-01-24T20:42:52Z");
  EcostressTimeTable tt(tstart);
  GeoCal::ImageCoordinateWithDerivative ic;
  ic.line = GeoCal::AutoDerivative<double>(5, 0, 2);
  ic.sample = GeoCal::AutoDerivative<double>(10, 1, 2);
  GeoCal::TimeWithDerivative t;
  GeoCal::FrameCoordinateWithDerivative fc;
  tt.time_with_derivative(ic, t, fc);
  blitz::Array<double, 2> jac_calc(3,2);
  jac_calc(0, blitz::Range::all()) = t.gradient();
  if(fc.line.is_constant())
    jac_calc(1, blitz::Range::all()) = 0;
  else
    jac_calc(1, blitz::Range::all()) = fc.line.gradient();
  if(fc.sample.is_constant())
    jac_calc(2, blitz::Range::all()) = 0;
  else
    jac_calc(2, blitz::Range::all()) = fc.sample.gradient();
  GeoCal::Time t0;
  GeoCal::FrameCoordinate fc0;
  tt.time(GeoCal::ImageCoordinate(5,10), t0, fc0);
  blitz::Array<double, 2> jac_fd(3,2);
  GeoCal::Time t1;
  GeoCal::FrameCoordinate fc1;
  double step = 0.1;
  tt.time(GeoCal::ImageCoordinate(5+step,10), t1, fc1);
  jac_fd(0,0) = (t1-t0)/step;
  jac_fd(1,0) = (fc1.line - fc0.line) / step;
  jac_fd(2,0) = (fc1.sample - fc0.sample) / step;
  tt.time(GeoCal::ImageCoordinate(5,10+step), t1, fc1);
  jac_fd(0,1) = (t1-t0)/step;
  jac_fd(1,1) = (fc1.line - fc0.line) / step;
  jac_fd(2,1) = (fc1.sample - fc0.sample) / step;
  // std::cerr << jac_calc << "\n"
  // 	    << jac_fd << "\n";
  BOOST_CHECK_MATRIX_CLOSE_TOL(jac_calc, jac_fd, 1e-4);
}

BOOST_AUTO_TEST_CASE(image_coordinate_jac_test)
{
  GeoCal::Time tstart = GeoCal::Time::parse_time("2015-01-24T20:42:52Z");
  EcostressTimeTable tt(tstart);
  GeoCal::Time t0;
  GeoCal::FrameCoordinate fc0;
  tt.time(GeoCal::ImageCoordinate(5,10), t0, fc0);
  GeoCal::TimeWithDerivative t = GeoCal::TimeWithDerivative::time_pgs
    (GeoCal::AutoDerivative<double>(t0.pgs(), 0, 3));
  GeoCal::FrameCoordinateWithDerivative fc;
  fc.line = GeoCal::AutoDerivative<double>(fc0.line, 1, 3);
  fc.sample = GeoCal::AutoDerivative<double>(fc0.sample, 2, 3);
  GeoCal::ImageCoordinateWithDerivative ic =
    tt.image_coordinate_with_derivative(t, fc);
  blitz::Array<double, 2> jac_calc(2,3);
  if(ic.line.is_constant())
    jac_calc(0, blitz::Range::all()) = 0;
  else
    jac_calc(0, blitz::Range::all()) = ic.line.gradient();
  if(ic.sample.is_constant())
    jac_calc(1, blitz::Range::all()) = 0;
  else
    jac_calc(1, blitz::Range::all()) = ic.sample.gradient();
  blitz::Array<double, 2> jac_fd(2,3);
  GeoCal::ImageCoordinate ic0 = tt.image_coordinate(t0, fc0);
  double step = 0.1;
  GeoCal::Time t1 = t0 + step;
  GeoCal::ImageCoordinate ic1 = tt.image_coordinate(t1, fc0);
  jac_fd(0,0) = (ic1.line - ic0.line) / step;
  jac_fd(1,0) = (ic1.sample - ic0.sample) / step;
  GeoCal::FrameCoordinate fc1(fc0.line + step, fc0.sample);
  ic1 = tt.image_coordinate(t0, fc1);
  jac_fd(0,1) = (ic1.line - ic0.line) / step;
  jac_fd(1,1) = (ic1.sample - ic0.sample) / step;
  GeoCal::FrameCoordinate fc2(fc0.line, fc0.sample + step);
  ic1 = tt.image_coordinate(t0, fc2);
  jac_fd(0,2) = (ic1.line - ic0.line) / step;
  jac_fd(1,2) = (ic1.sample - ic0.sample) / step;
  // std::cerr << jac_calc << "\n"
  // 	    << jac_fd << "\n";
  BOOST_CHECK_MATRIX_CLOSE_TOL(jac_calc, jac_fd, 1e-2);
}

BOOST_AUTO_TEST_CASE(read_file)
{
  EcostressTimeTable tt(test_data_dir() + "ECOSTRESS_L1A_PIX_80005_001_20150124T204250_0100_02.h5.expected");
  EcostressTimeTable tt2(test_data_dir() + "ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5.expected");
  BOOST_CHECK_EQUAL(tt.averaging_done(), false);
  BOOST_CHECK_EQUAL(tt2.averaging_done(), true);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  GeoCal::Time tstart = GeoCal::Time::parse_time("2015-01-24T20:42:52Z");
  boost::shared_ptr<GeoCal::TimeTable> tt =
    boost::make_shared<EcostressTimeTable>(tstart);
  std::string d = GeoCal::serialize_write_string(tt);
  if(false)
    std::cerr << d;
  boost::shared_ptr<GeoCal::TimeTable> ttr =
    GeoCal::serialize_read_string<GeoCal::TimeTable>(d);
  BOOST_CHECK_EQUAL(tt->max_line(), ttr->max_line());
}

BOOST_AUTO_TEST_SUITE_END()
