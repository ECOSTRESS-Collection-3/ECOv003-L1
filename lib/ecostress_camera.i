// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "geocal_time.h"
#include "ecostress_camera.h"
%}

%geocal_base_import(quaternion_camera)
%include "ecostress_paraxial_transform.i"

%ecostress_shared_ptr(Ecostress::EcostressCamera);
namespace Ecostress {
class EcostressCamera : public GeoCal::QuaternionCamera {
public:
  EcostressCamera(double Focal_length, double Y_scale,
		  double Y_offset,
		  boost::math::quaternion<double> Frame_to_sc_q);
  void mask_all_parameter();
  %python_attribute_with_set(paraxial_transform, boost::shared_ptr<EcostressParaxialTransform>);
  %python_attribute_with_set(y_scale, double);
  %python_attribute_with_set(y_offset, double);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressCamera")
