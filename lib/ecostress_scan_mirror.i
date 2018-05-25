// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_scan_mirror.h"
%}

%base_import(generic_object)
%import "image_coordinate.i"

%ecostress_shared_ptr(Ecostress::EcostressScanMirror);
namespace Ecostress {
class EcostressScanMirror : public GeoCal::GenericObject {
public:
  EcostressScanMirror(double Scan_start = -25.5, double Scan_end = 25.5,
		      int Number_sample = 5400);
  double scan_mirror_angle(int Scan_index, double Ic_sample) const;
  GeoCal::AutoDerivative<double> scan_mirror_angle
  (int Scan_index, const GeoCal::AutoDerivative<double>& Ic_sample) const;
  boost::math::quaternion<double>
  rotation_quaternion(int Scan_index, double Ic_sample) const;
  boost::math::quaternion<GeoCal::AutoDerivative<double> >
  rotation_quaternion(int Scan_index,
		     const GeoCal::AutoDerivative<double>& Ic_sample) const;
  %python_attribute(number_sample, int);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressScanMirror")
