// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "geocal_time.h"
#include "ecostress_camera.h"
%}

%geocal_base_import(quaternion_camera)

%ecostress_shared_ptr(Ecostress::EcostressCamera);
namespace Ecostress {
class EcostressCamera : public GeoCal::QuaternionCamera {
public:
  EcostressCamera();
  // Not ready for this yet
  //  %pickle_serialization();
};
}

