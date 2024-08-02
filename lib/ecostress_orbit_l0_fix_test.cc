#include "unit_test_support.h"
#include "ecostress_orbit_l0_fix.h"
#include "geocal/geodetic.h"
using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ecostress_orbit_l0_fix, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  EcostressOrbitL0Fix orb(unit_test_data_dir() + "L1A_RAW_ATT_00049_20180709T214305_0400_01.h5");
  boost::shared_ptr<GeoCal::CartesianFixed> pos;
  GeoCal::Time tdata_start = GeoCal::Time::parse_time("2018-07-09T21:43:05.015151Z");
  GeoCal::Time tdata_end = GeoCal::Time::parse_time("2018-07-09T22:51:24.012658Z");
  GeoCal::Time tgap_start = tdata_start + 74;
  GeoCal::Time tgap_end = tdata_start + 4025.99751;

  BOOST_CHECK(!orb.spacecraft_x_mostly_in_velocity_direction(tdata_start + 3.0));
  
  // Should be able to get orbit data for times a little before and
  // after the data
  BOOST_CHECK_NO_THROW(pos=orb.position_cf(tdata_start - 3.0));
  BOOST_CHECK_NO_THROW(pos=orb.position_cf(tdata_end + 3.0));
  if(false) {
    GeoCal::Geodetic p0(*orb.position_cf(tdata_start - 3.0));
    for(double toffset = -3.0; toffset < 3.0 ; toffset += 1.0)
      std::cerr << toffset << ": "
		<< GeoCal::Geodetic(*orb.position_cf(tdata_start + toffset))
		<< " " << GeoCal::distance(p0,
	        *orb.position_cf(tdata_start + toffset)) << "\n";
    p0 = GeoCal::Geodetic(*orb.position_cf(tdata_end - 3.0));
    for(double toffset = -3.0; toffset < 3.0 ; toffset += 1.0)
      std::cerr << toffset << ": "
		<< GeoCal::Geodetic(*orb.position_cf(tdata_end + toffset))
		<< " " << GeoCal::distance(p0,
	        *orb.position_cf(tdata_end + toffset)) << "\n";
  }				     
  
  // Should be able to get orbit data in the gap for times near the ends.
  BOOST_CHECK_NO_THROW(pos=orb.position_cf(tgap_start + 3.0));
  BOOST_CHECK_NO_THROW(pos=orb.position_cf(tgap_end - 3.0));

  if(false) {
    GeoCal::Geodetic p0(*orb.position_cf(tgap_start - 3.0));
    for(double toffset = -3.0; toffset < 3.0 ; toffset += 1.0)
      std::cerr << toffset << ": "
		<< GeoCal::Geodetic(*orb.position_cf(tgap_start + toffset))
		<< " " << GeoCal::distance(p0,
	        *orb.position_cf(tgap_start + toffset)) << "\n";
    p0 = GeoCal::Geodetic(*orb.position_cf(tgap_end - 3.0));
    for(double toffset = -3.0; toffset < 3.0 ; toffset += 1.0)
      std::cerr << toffset << ": "
		<< GeoCal::Geodetic(*orb.position_cf(tgap_end + toffset))
		<< " " << GeoCal::distance(p0,
	        *orb.position_cf(tgap_end + toffset)) << "\n";
  }				     

  // Should not be able to get data in the middle of the large gap, or
  // way past our end points
  BOOST_CHECK_THROW(pos=orb.position_cf(tgap_start + 20), GeoCal::Exception);
  BOOST_CHECK_THROW(pos=orb.position_cf(tgap_end - 20), GeoCal::Exception);
  BOOST_CHECK_THROW(pos=orb.position_cf(tdata_start - 20), GeoCal::Exception);
  BOOST_CHECK_THROW(pos=orb.position_cf(tdata_end + 20), GeoCal::Exception);
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<EcostressOrbitL0Fix> orb =
    boost::make_shared<EcostressOrbitL0Fix>(unit_test_data_dir() + "L1A_RAW_ATT_00049_20180709T214305_0400_01.h5");
  std::string d = GeoCal::serialize_write_string(orb);
  if(false)
    std::cerr << d;
  boost::shared_ptr<GeoCal::Orbit> orbr =
    GeoCal::serialize_read_string<GeoCal::Orbit>(d);
  BOOST_CHECK_CLOSE(orb->min_time().pgs(), orbr->min_time().pgs(), 1e-4);
  BOOST_CHECK_CLOSE(orb->max_time().pgs(), orbr->max_time().pgs(), 1e-4);
}

BOOST_AUTO_TEST_SUITE_END()
