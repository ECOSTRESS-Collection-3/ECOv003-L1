// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "simulated_radiance.h"
%}

%base_import(generic_object)
%import "ground_coordinate_array.i"
%import "raster_image.i"

%ecostress_shared_ptr(Ecostress::SimulatedRadiance);
namespace Ecostress {
class SimulatedRadiance : public GeoCal::GenericObject {
public:
  SimulatedRadiance(const boost::shared_ptr<GroundCoordinateArray>& Gca,
	    const boost::shared_ptr<GeoCal::RasterImage>& Map_projected_image, 
	    int Avg_fact = -1,
	    bool Read_into_memory = false,
	    double Fill_value = 0.0);
  blitz::Array<double, 2> radiance_scan(int Start_line, int Number_line=-1)
    const;
  %python_attribute(ground_coordinate_array,
		    boost::shared_ptr<GroundCoordinateArray>);
  %python_attribute(avg_factor, int);
  %python_attribute(fill_value, double);
  %python_attribute(read_into_memory, bool);
  %python_attribute(map_projected_image,
		    boost::shared_ptr<GeoCal::RasterImage>);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("SimulatedRadiance")
