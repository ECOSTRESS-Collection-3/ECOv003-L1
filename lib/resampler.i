// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "resampler.h"
%}

%base_import(generic_object)
%import "raster_image.i"
%import "map_info.i"

%ecostress_shared_ptr(Ecostress::Resampler);
namespace Ecostress {
class Resampler : public GeoCal::GenericObject {
public:
  Resampler(const boost::shared_ptr<GeoCal::RasterImage>& Latitude,
	    const boost::shared_ptr<GeoCal::RasterImage>& Longitude,
	    const GeoCal::MapInfo& Mi, int Num_sub_pixel = 2,
	    bool Exactly_match_mi = false);
  void resample_field(const std::string& Fname,
		      const boost::shared_ptr<GeoCal::RasterImage>& Data,
		      double Scale_data=1.0,
		      const std::string& File_type="REAL",
		      bool Negative_to_zero=false);
  %python_attribute(map_info, const GeoCal::MapInfo&);
  %python_attribute(number_sub_pixel, int);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("Resampler")
