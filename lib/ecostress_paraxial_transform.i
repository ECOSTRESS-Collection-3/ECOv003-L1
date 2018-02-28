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
  void paraxial_to_real(double Paraxial_x,
			double Paraxial_y, double& OUTPUT, 
			double& OUTPUT) const;
  void paraxial_to_real(const GeoCal::AutoDerivative<double>& Paraxial_x,
			const GeoCal::AutoDerivative<double>& Paraxial_y,
			GeoCal::AutoDerivative<double>& OUTPUT, 
			GeoCal::AutoDerivative<double>& OUTPUT) const;
  void real_to_paraxial(double Real_x,
			double Real_y, double& OUTPUT, 
			double& OUTPUT) const;
  void real_to_paraxial(const GeoCal::AutoDerivative<double>& Real_x,
			const GeoCal::AutoDerivative<double>& Real_y,
			GeoCal::AutoDerivative<double>& OUTPUT, 
			GeoCal::AutoDerivative<double>& OUTPUT) const;
  std::string print_to_string() const;
  %python_attribute(real_to_par, blitz::Array<double, 2>&);
  %python_attribute(par_to_real, blitz::Array<double, 2>&);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressParaxialTransform")

