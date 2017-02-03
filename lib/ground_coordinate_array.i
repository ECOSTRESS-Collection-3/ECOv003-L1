// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ground_coordinate_array.h"
%}

%base_import(generic_object)
%import "ecostress_image_ground_connection.i"

%ecostress_shared_ptr(Ecostress::GroundCoordinateArray);
namespace Ecostress {
class GroundCoordinateArray : public GeoCal::GenericObject {
public:
  GroundCoordinateArray(const boost::shared_ptr<EcostressImageGroundConnection>& Igc);
  %python_attribute(igc, boost::shared_ptr<EcostressImageGroundConnection>);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

