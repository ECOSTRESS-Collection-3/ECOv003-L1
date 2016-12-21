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
  EcostressScanMirror(double Scan_start = 25.5, double Scan_end = -25.5,
		      int Number_sample = 5400);
  double scan_mirror_angle(const GeoCal::ImageCoordinate& Ic) const;
  boost::math::quaternion<double>
    rotation_quaterion(const GeoCal::ImageCoordinate& Ic) const;
  %python_attribute(scan_start, double);
  %python_attribute(scan_end, double);
  %python_attribute(number_sample, int);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

