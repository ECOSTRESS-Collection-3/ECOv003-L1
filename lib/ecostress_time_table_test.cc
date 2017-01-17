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
  BOOST_CHECK_EQUAL(tt.max_line(), 44 * tt.number_line_scan());
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc;
  tt.time(GeoCal::ImageCoordinate(0, 0), t, fc);
  BOOST_CHECK(fabs(t - tstart) < 1e-6);
  BOOST_CHECK_CLOSE(fc.line, 0, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  tt.time(GeoCal::ImageCoordinate(0, 20.4), t, fc);
  BOOST_CHECK(fabs(t -
		   (tstart + 20.4 * EcostressTimeTable::frame_time)) < 1e-6);
  BOOST_CHECK_CLOSE(fc.line, 0, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  tt.time(GeoCal::ImageCoordinate(127.4, 0), t, fc);
  BOOST_CHECK(fabs(t - tstart) < 1e-6);
  BOOST_CHECK_CLOSE(fc.line, 127.4, 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  tt.time(GeoCal::ImageCoordinate(128.6, 0), t, fc);
  BOOST_CHECK(fabs(t -
     (tstart + 1 * EcostressTimeTable::nominal_scan_spacing) < 1e-6));
  BOOST_CHECK_CLOSE(fc.line, 128.6 - 1 * tt.number_line_scan(), 1e-4);
  BOOST_CHECK_CLOSE(fc.sample, 0, 1e-4);
  for(int i = 0; i < tt.max_line(); i+=10)
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
