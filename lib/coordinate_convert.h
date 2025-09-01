#include "geocal/ogr_coordinate.h"
#include "geocal/gdal_raster_image.h"
#include <boost/make_shared.hpp>
namespace Ecostress {
  blitz::Array<double, 2> coordinate_convert(const blitz::Array<double, 1>& latitude,
					     const blitz::Array<double, 1>& longitude,
					     const boost::shared_ptr<GeoCal::OgrWrapper>& ogr);
  void set_fill_value(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Fill_value);
  void set_scale(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Scale_value);
  void set_offset(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Offset_value);
  void write_data(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, const blitz::Array<double, 2>& Data);
  void write_gdal(const std::string& Fname, const std::string& Driver_name,
		  const GeoCal::GdalRasterImage& Img, const std::string& Options);
  boost::shared_ptr<GeoCal::GdalRasterImage> gdal_band(
      const boost::shared_ptr<GeoCal::GdalRasterImage>& G, int B)
  { return boost::make_shared<GeoCal::GdalRasterImage>(G->data_set(), B); }
  std::string to_proj4(const boost::shared_ptr<GeoCal::OgrCoordinate>& G);
  // Geocal doesn't export copy to python. Probably should and just
  // rename it, but for now we just do this here.
  void copy_raster(const GeoCal::RasterImage& Img_in, GeoCal::RasterImage& Img_out, bool diagnostic = false, int Tile_nline = -1, int Tile_nsamp = -1)
  { GeoCal::copy(Img_in, Img_out, diagnostic, Tile_nline, Tile_nsamp); }
}
