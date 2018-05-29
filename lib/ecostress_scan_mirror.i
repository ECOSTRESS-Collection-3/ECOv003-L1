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
  EcostressScanMirror(double Scan_start = -26.488105667851173,
		      double Scan_end = 26.488105667851173,
		      int Number_sample = 5400,
		      int Number_scan = 44,
		      int Max_encoder_value = 1749248,
		      int First_encoder_value_at_0 = 401443,
		      int Second_encoder_value_at_0 = 1275903);
  EcostressScanMirror(const blitz::Array<int, 2>& Encoder_value,
		      int Max_encoder_value = 1749248,
		      int First_encoder_value_at_0 = 401443,
		      int Second_encoder_value_at_0 = 1275903
		      );
  double scan_mirror_angle(int Scan_index, double Ic_sample) const;
  GeoCal::AutoDerivative<double> scan_mirror_angle
  (int Scan_index, const GeoCal::AutoDerivative<double>& Ic_sample) const;
  boost::math::quaternion<double>
  rotation_quaternion(int Scan_index, double Ic_sample) const;
  boost::math::quaternion<GeoCal::AutoDerivative<double> >
  rotation_quaternion(int Scan_index,
		     const GeoCal::AutoDerivative<double>& Ic_sample) const;
  double angle_from_encoder_value(double Evalue) const;
  GeoCal::AutoDerivative<double> angle_from_encoder_value
  (const GeoCal::AutoDerivative<double>& Evalue) const;
  int angle_to_encoder_value(double Angle_deg, int Mirror_side) const;
  double encoder_value_interpolate(int Scan_index, double Ic_sample) const;
  GeoCal::AutoDerivative<double>
  encoder_value_interpolate(int Scan_index,
    const GeoCal::AutoDerivative<double> Ic_sample) const;
  %python_attribute(first_encoder_value_at_0, int);
  %python_attribute(second_encoder_value_at_0, int);
  %python_attribute(angle_per_encoder_value, double);
  %python_attribute(number_sample, int);
  %python_attribute(number_scan, int);
  %python_attribute(encoder_value, blitz::Array<int, 2>);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressScanMirror")
