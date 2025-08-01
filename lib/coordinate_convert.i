// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "coordinate_convert.h"
#include <geocal/camera.h>
#include <geocal/ecr.h>
#include <geocal/planet_coordinate.h>
#include <geocal/image_ground_connection.h>
%}
%import "ogr_coordinate.i"
%import "gdal_raster_image.i"
namespace Ecostress {
  blitz::Array<double, 2> coordinate_convert(const blitz::Array<double, 1>& latitude,
					     const blitz::Array<double, 1>& longitude,
					     const boost::shared_ptr<GeoCal::OgrWrapper>& ogr);
  void set_fill_value(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Fill_value);
  void write_data(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, const blitz::Array<double, 2>& Data);
  void write_gdal(const std::string& Fname, const std::string& Driver_name,
		  const GeoCal::GdalRasterImage& Img, const std::string& Options);
  boost::shared_ptr<GeoCal::GdalRasterImage> gdal_band(const boost::shared_ptr<GeoCal::GdalRasterImage>& G, int B);
  std::string to_proj4(const boost::shared_ptr<GeoCal::OgrCoordinate>& G);
}

// List of things "import *" will include
%python_export("coordinate_convert", "set_fill_value", "write_data", "write_gdal", "gdal_band",
	       "to_proj4")
