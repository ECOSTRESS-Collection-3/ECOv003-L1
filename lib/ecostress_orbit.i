// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_orbit.h"
%}

%geocal_base_import(hdf_orbit)

%ecostress_shared_ptr(Ecostress::EcostressOrbit);
namespace Ecostress {
class EcostressOrbit : public GeoCal::HdfOrbit<GeoCal::Eci, GeoCal::TimeJ2000Creator> {
public:
  EcostressOrbit(const std::string& Fname, double Extrapolation_pad = 5.0,
		 double Large_gap = 10.0);
  EcostressOrbit(const std::string& Fname,
		 const blitz::Array<double, 1>& Pos_off,
		 double Extrapolation_pad = 5.0,
		 double Large_gap = 10.0);
  bool spacecraft_x_mostly_in_velocity_direction(GeoCal::Time T) const;
  %python_attribute_with_set(large_gap, double);
  %python_attribute_with_set(extrapolation_pad, double);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressOrbit")
