// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ground_coordinate_array.h"
%}

%base_import(generic_object)
%import "ecostress_image_ground_connection.i"
%import "memory_raster_image.i"
%import "vicar_lite_file.i"

%ecostress_shared_ptr(Ecostress::GroundCoordinateArray);
namespace Ecostress {
class GroundCoordinateArray : public GeoCal::GenericObject {
public:
  GroundCoordinateArray
  (const boost::shared_ptr<EcostressImageGroundConnection>& Igc,
   bool Include_angle=false, int Nsub_line = 1, int Nsub_sample = 1);
  %python_attribute(igc, boost::shared_ptr<EcostressImageGroundConnection>);
  blitz::Array<double,5> ground_coor_arr() const;
  blitz::Array<double,5>
  ground_coor_scan_arr(int Start_line, int Number_line=-1) const;
  GeoCal::MapInfo cover(double Resolution=70.0) const;
  GeoCal::MapInfo cover(const GeoCal::MapInfo& Mi) const;
  boost::shared_ptr<GeoCal::MemoryRasterImage>
  raster_cover(double Resolution=70.0) const;
  boost::shared_ptr<GeoCal::MemoryRasterImage>
  raster_cover(const GeoCal::MapInfo& Mi) const;
  boost::shared_ptr<GeoCal::VicarLiteRasterImage>
  raster_cover_vicar(const std::string& Fname, double Resolution=70.0) const;
  boost::shared_ptr<GeoCal::VicarLiteRasterImage>
  raster_cover_vicar(const std::string& Fname, const GeoCal::MapInfo& Mi) const;
  boost::shared_ptr<GeoCal::MemoryRasterImage>
  GroundCoordinateArray::project_surface(double Resolution=70.0) const;
  void GroundCoordinateArray::project_surface_scan_arr
  (GeoCal::RasterImage& Data, int Start_line, int Number_line) const;
  static blitz::Array<double, 2>
  interpolate(const GeoCal::RasterImage& Data,
	      const blitz::Array<double, 2>& Lat,
	      const blitz::Array<double, 2>& Lon);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("GroundCoordinateArray")
