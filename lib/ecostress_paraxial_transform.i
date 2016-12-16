// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_paraxial_transform.h"
%}

%geocal_base_import(generic_object)
%import "auto_derivative.i"

%ecostress_shared_ptr(Ecostress::EcostressParaxialTransform);
namespace Ecostress {
class EcostressParaxialTransform : public GeoCal::GenericObject {
public:
  EcostressParaxialTransform();
  std::string print_to_string() const;
  %python_attribute(real_to_paraxial, blitz::Array<double, 2>&);
  %python_attribute(paraxial_to_real, blitz::Array<double, 2>&);
  %pickle_serialization();
};
}

