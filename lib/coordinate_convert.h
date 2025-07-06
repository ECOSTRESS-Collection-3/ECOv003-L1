#include "geocal/ogr_coordinate.h"
#include "geocal/gdal_raster_image.h"
#include <boost/make_shared.hpp>
namespace Ecostress {
  blitz::Array<double, 2> coordinate_convert(const blitz::Array<double, 1>& latitude,
					     const blitz::Array<double, 1>& longitude,
					     const boost::shared_ptr<GeoCal::OgrWrapper>& ogr);
  void set_fill_value(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Fill_value);
  void write_data(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, const blitz::Array<double, 2>& Data);
  void write_gdal(const std::string& Fname, const std::string& Driver_name,
		  const GeoCal::GdalRasterImage& Img, const std::string& Options);
  boost::shared_ptr<GeoCal::GdalRasterImage> gdal_band(
      const boost::shared_ptr<GeoCal::GdalRasterImage>& G, int B)
  { return boost::make_shared<GeoCal::GdalRasterImage>(G->data_set(), B); }
}
