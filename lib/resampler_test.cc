#include "unit_test_support.h"
#include "resampler.h"
#include "geocal/gdal_raster_image.h"
#include "geocal/landsat7_global.h"
#include <boost/make_shared.hpp>
using namespace Ecostress;
using namespace GeoCal;

BOOST_FIXTURE_TEST_SUITE(resampler, GlobalFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  // Skip if we don't have landsat data available.
  if(landsat7_dir() == "")
    return;
  // This is a fairly slow test, so skip normally. We can turn this
  // on if there are any issues
  return;
  std::string fname = test_data_dir() + "ECOSTRESS_L1B_GEO_80005_001_20150124T204250_0100_01.h5.expected";
  std::string fname2 = test_data_dir() + "ECOSTRESS_L1B_RAD_80005_001_20150124T204250_0100_01.h5.expected";
  boost::shared_ptr<GdalRasterImage> lat = boost::make_shared<GdalRasterImage>("HDF5:\"" + fname + "\"://Geolocation/latitude");
  boost::shared_ptr<GdalRasterImage> lon = boost::make_shared<GdalRasterImage>("HDF5:\"" + fname + "\"://Geolocation/longitude");
  boost::shared_ptr<GdalRasterImage> swir_dn = boost::make_shared<GdalRasterImage>("HDF5:\"" + fname2 + "\"://SWIR/swir_dn");
  Landsat7Global orth(landsat7_dir(), Landsat7Global::BAND5);
  MapInfo mi = orth.map_info().scale(2, 2);
  Resampler r(lat, lon, mi);
  r.resample_field("swir_res.img", swir_dn);
}

// Don't actually test for serialization. The data is really pretty
// big, larger than we want to write out as XML. We could possibly
// write out binary data for some special case thing, but for now just
// assume serialization is working if we every need it.
// BOOST_AUTO_TEST_CASE(serialization)
//{
//}
BOOST_AUTO_TEST_SUITE_END()
