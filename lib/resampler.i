// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "resampler.h"
%}

%base_import(generic_object)
%import "raster_image.i"
%import "map_info.i"
%import "dem.i"

%ecostress_shared_ptr(Ecostress::Resampler);
namespace Ecostress {
class Resampler : public GeoCal::GenericObject {
public:
  Resampler(const boost::shared_ptr<GeoCal::RasterImage>& Latitude,
	    const boost::shared_ptr<GeoCal::RasterImage>& Longitude,
	    const GeoCal::MapInfo& Mi, int Num_sub_pixel = 2,
	    bool Exactly_match_mi = false);
  Resampler(const blitz::Array<double, 2>& Latitude_interpolated,
	    const blitz::Array<double, 2>& Longitude_interpolated,
	    const GeoCal::MapInfo& Mi, int Num_sub_pixel = 2,
	    bool Exactly_match_mi = false);
  blitz::Array<double, 2> resample_field
  (const boost::shared_ptr<GeoCal::RasterImage>& Data,
   double Scale_data=1.0,
   bool Negative_to_zero=false, double Fill_value = 0.0,
   bool Use_smallest_ic=false) const;
  void resample_field(const std::string& Fname,
		      const boost::shared_ptr<GeoCal::RasterImage>& Data,
		      double Scale_data=1.0,
		      const std::string& File_type="REAL",
		      bool Negative_to_zero=false, double Fill_value = 0.0) const;
  void map_values(const GeoCal::Dem& d,
		  blitz::Array<double, 2>& OUTPUT,
		  blitz::Array<double, 2>& OUTPUT,
		  blitz::Array<double, 2>& OUTPUT) const;
  %python_attribute(map_info, const GeoCal::MapInfo&);
  %python_attribute(number_sub_pixel, int);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("Resampler")
