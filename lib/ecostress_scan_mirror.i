// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_scan_mirror.h"
%}

%base_import(observer)
%base_import(with_parameter)
%import "image_coordinate.i"

%ecostress_shared_ptr(Ecostress::EcostressScanMirror);
%ecostress_shared_ptr(GeoCal::Observable<Ecostress::EcostressScanMirror>);
%ecostress_shared_ptr(GeoCal::Observer<Ecostress::EcostressScanMirror>);
namespace GeoCal {
%template(ObservableEcostressScanMirror) GeoCal::Observable<Ecostress::EcostressScanMirror>;
%template(ObserverEcostressScanMirror) GeoCal::Observer<Ecostress::EcostressScanMirror>;
}
namespace Ecostress {
class EcostressScanMirror : public GeoCal::Observable<Ecostress::EcostressScanMirror>, public GeoCal::WithParameter {
public:
  EcostressScanMirror(double Scan_start = -26.488105667851173,
		      double Scan_end = 26.488105667851173,
		      int Number_sample = 5400,
		      int Number_scan = 44,
		      int Max_encoder_value = 1749248,
		      double First_encoder_value_at_0 = 401443,
		      double Second_encoder_value_at_0 = 1275903,
		      double Epsilon = 0,
		      double Beta = 0,
		      double Delta = 0,
		      double First_angle_per_ev = 360.0 / 1749248 * 2,
		      double Second_angle_per_ev = 360.0 / 1749248 * 2
		      );
  EcostressScanMirror(const blitz::Array<int, 2>& Encoder_value,
		      int Max_encoder_value = 1749248,
		      double First_encoder_value_at_0 = 401443,
		      double Second_encoder_value_at_0 = 1275903,
		      double Epsilon = 0,
		      double Beta = 0,
		      double Delta = 0,
		      double First_angle_per_ev = 360.0 / 1749248 * 2,
		      double Second_angle_per_ev = 360.0 / 1749248 * 2
		      );
  virtual void add_observer(GeoCal::Observer<EcostressScanMirror>& Obs);
  virtual void remove_observer(GeoCal::Observer<EcostressScanMirror>& Obs);
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
  %python_attribute_with_set(instrument_to_sc, boost::math::quaternion<double>)
  %python_attribute_with_set(instrument_to_sc_with_derivative, 
			     boost::math::quaternion<GeoCal::AutoDerivative<double> >)
  %python_attribute_with_set(euler, blitz::Array<double, 1>);
  %python_attribute_with_set(euler_with_derivative, 
			     blitz::Array<GeoCal::AutoDerivative<double>, 1>);
  %python_attribute_with_set(fit_epsilon, bool);
  %python_attribute_with_set(fit_beta, bool);
  %python_attribute_with_set(fit_delta, bool);
  %python_attribute_with_set(fit_first_encoder_value_at_0, bool);
  %python_attribute_with_set(fit_second_encoder_value_at_0, bool);
  %python_attribute_with_set(fit_first_angle_per_encoder_value, bool);
  %python_attribute_with_set(fit_second_angle_per_encoder_value, bool);
  %python_attribute(first_encoder_value_at_0, double);
  %python_attribute(first_encoder_value_at_0_with_derivative, GeoCal::AutoDerivative<double>);
  %python_attribute(second_encoder_value_at_0, double);
  %python_attribute(second_encoder_value_at_0_with_derivative, GeoCal::AutoDerivative<double>);
  %python_attribute(first_angle_per_encoder_value, double);
  %python_attribute(second_angle_per_encoder_value, double);
  %python_attribute(first_angle_per_encoder_value_with_derivative, GeoCal::AutoDerivative<double>);
  %python_attribute(second_angle_per_encoder_value_with_derivative, GeoCal::AutoDerivative<double>);
  %python_attribute(number_sample, int);
  %python_attribute(number_scan, int);
  %python_attribute(encoder_value, blitz::Array<int, 2>);
  std::string print_to_string() const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressScanMirror", "ObserverEcostressScanMirror", "ObservableEcostressScanMirror")
