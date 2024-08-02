// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_orbit_l0_fix.h"
%}

%geocal_base_import(orbit_array)

%ecostress_shared_ptr(Ecostress::EcostressOrbitL0Fix);
namespace Ecostress {
class EcostressOrbitL0Fix : public GeoCal::OrbitArray<GeoCal::Eci, GeoCal::TimeJ2000Creator> {
public:
  EcostressOrbitL0Fix(const std::string& Fname, double Extrapolation_pad = 5.0,
		      double Large_gap = 10.0, bool Apply_fix = true);
  EcostressOrbitL0Fix(const std::string& Fname,
		 const blitz::Array<double, 1>& Pos_off,
		 double Extrapolation_pad = 5.0,
		 double Large_gap = 10.0, bool Apply_fix = true);
  static double fix_l0_j2000_time(double Wrong_j2000_time);
  static blitz::Array<double, 1>
  fix_l0_j2000_time(const blitz::Array<double, 1>& Wrong_j2000_time);
  %python_attribute(file_name, std::string)
  %python_attribute(apply_fix, bool)
  bool spacecraft_x_mostly_in_velocity_direction(GeoCal::Time T) const;
  %python_attribute_with_set(large_gap, double);
  %python_attribute_with_set(extrapolation_pad, double);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressOrbitL0Fix")
