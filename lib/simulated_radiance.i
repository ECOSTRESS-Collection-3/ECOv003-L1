// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "simulated_radiance.i"
%}

%base_import(generic_object)
%import "ground_coordinate_array.i"

%ecostress_shared_ptr(Ecostress::SimulatedRadiance);
namespace Ecostress {
class SimulatedRadiance : public GeoCal::GenericObject {
public:
  SimulatedRadiance(const boost::shared_ptr<GroundCoordinateArray>& Gca);
  %python_attribute(ground_coordinate_array,
		    boost::shared_ptr<GroundCoordinateArray>);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

