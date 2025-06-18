// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "resampler.h"
#include "geocal/image_ground_connection.h"
%}

%base_import(generic_object)
%import "raster_image.i"
%import "map_info.i"
%import "dem.i"

%ecostress_shared_ptr(Ecostress::Resampler);
namespace Ecostress {
class Resampler : public GeoCal::GenericObject {
public:
  Resampler(const boost::shared_ptr<GeoCal::RasterImage>& X_coor,
	    const boost::shared_ptr<GeoCal::RasterImage>& Y_coor,
	    const GeoCal::MapInfo& Mi, int Num_sub_pixel = 2,
	    bool Exactly_match_mi = false,
	    double Mark_missing=-1000.0);
  Resampler(const blitz::Array<double, 2>& X_coor_interpolated,
	    const blitz::Array<double, 2>& Y_coor_interpolated,
	    const GeoCal::MapInfo& Mi, int Num_sub_pixel = 2,
	    bool Exactly_match_mi = false,
	    double Mark_missing=-1000.0);
  bool empty_resample() const;
  blitz::Array<double, 2> resample_field
  (const boost::shared_ptr<GeoCal::RasterImage>& Data,
   double Scale_data=1.0,
   bool Negative_to_zero=false, double Fill_value = 0.0,
   bool Use_smallest_ic=false) const;
  blitz::Array<int, 2> resample_dqi
  (const boost::shared_ptr<GeoCal::RasterImage>& Data) const;
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
