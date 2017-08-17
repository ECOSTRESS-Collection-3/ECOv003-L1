#include "unit_test_support.h"
#include "ground_coordinate_array.h"
#include "ecostress_igc_fixture.h"
#include "geocal/srtm_dem.h"
#include "geocal/geodetic.h"
#include "geocal/gdal_raster_image.h"

using namespace Ecostress;

BOOST_FIXTURE_TEST_SUITE(ground_coordinate_array, EcostressIgcFixture)

BOOST_AUTO_TEST_CASE(basic_test)
{
  GroundCoordinateArray gca(igc);
  GroundCoordinateArray gca_hres(igc_hres);
  blitz::Array<double, 3> res = gca.ground_coor_scan_arr(4, 20);
  blitz::Array<double, 3> res_hres = gca_hres.ground_coor_scan_arr(4*2, 20*2);
  BOOST_CHECK_EQUAL(res.rows(), 20);
  BOOST_CHECK_EQUAL(res.cols(), 5400);
  BOOST_CHECK_EQUAL(res.depth(), 3);
  GeoCal::Geodetic pt(res(10-4,20,0),res(10-4,20,1),res(10-4,20,2));
  GeoCal::Geodetic pt_hres(res_hres(20-8,20,0),res_hres(20-8,20,1),
			   res_hres(20-8,20,2));
  BOOST_CHECK(distance(pt, *igc->ground_coordinate(GeoCal::ImageCoordinate(10, 20))) < 1.0);
  BOOST_CHECK(distance(pt_hres, *igc_hres->ground_coordinate(GeoCal::ImageCoordinate(20, 20))) < 1.0);
  BOOST_CHECK(distance(pt_hres, pt) < 1.0);
}

BOOST_AUTO_TEST_CASE(projection_test)
{
  // Don't normally run this, it takes a bit of time for a unit test
  // (about 35 seconds on pistol)
  return;
  GroundCoordinateArray gca(igc);
  boost::shared_ptr<GeoCal::MemoryRasterImage> ras = gca.raster_cover();
  BOOST_CHECK_EQUAL(ras->number_line(), 7586);
  BOOST_CHECK_EQUAL(ras->number_sample(), 9532);
  std::cerr << *ras << "\n";
  std::cerr << ras->coordinate(*igc->ground_coordinate(GeoCal::ImageCoordinate(0,0)))
	    << "\n"
	    << ras->coordinate(*igc->ground_coordinate(
	    GeoCal::ImageCoordinate(0,igc->number_sample() -1))) << "\n"
	    << ras->coordinate(*igc->ground_coordinate(
	    GeoCal::ImageCoordinate(igc->number_line() -1 ,igc->number_sample() -1))) << "\n"
	    << ras->coordinate(*igc->ground_coordinate(
						      GeoCal::ImageCoordinate(igc->number_line() -1, 0))) << "\n";
  for(int lstart = 0 ; lstart < igc->number_line();
      lstart += igc->number_line_scan())
    gca.project_surface_scan_arr(*ras, lstart);
  GeoCal::GdalRasterImage::save("proj.tif", "GTIFF", *ras,
				GeoCal::GdalRasterImage::Int16);
}

BOOST_AUTO_TEST_CASE(full_test)
{
  // Don't normally run this, it takes a bit of time for a unit test
  // (about 35 seconds on pistol)
  return;
  GroundCoordinateArray gca(igc);
  blitz::Array<double, 3> res = gca.ground_coor_arr();
}

BOOST_AUTO_TEST_CASE(serialization)
{
  boost::shared_ptr<GroundCoordinateArray> gca =
    boost::make_shared<GroundCoordinateArray>(igc);
  std::string d = GeoCal::serialize_write_string(gca);
  if(false)
    std::cerr << d;
  boost::shared_ptr<GroundCoordinateArray> igcr =
    GeoCal::serialize_read_string<GroundCoordinateArray>(d);
}

BOOST_AUTO_TEST_SUITE_END()
