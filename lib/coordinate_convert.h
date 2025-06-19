#include "geocal/ogr_coordinate.h"
#include "geocal/gdal_raster_image.h"
namespace Ecostress {
  blitz::Array<double, 2> coordinate_convert(const blitz::Array<double, 1> latitude,
					     const blitz::Array<double, 1> longitude,
					     const boost::shared_ptr<GeoCal::OgrWrapper>& ogr);
  void set_fill_value(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Fill_value);
}
