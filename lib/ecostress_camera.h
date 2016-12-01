#ifndef ECOSTRESS_CAMERA_H
#define ECOSTRESS_CAMERA_H
#include "geocal/quaternion_camera.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress camera model.

  Right now we don't model the optical nonlinearity. We'll add that in
  later.
*******************************************************************/

class EcostressCamera : public GeoCal::QuaternionCamera {
public:
  EcostressCamera();
  virtual ~EcostressCamera() {}
  virtual void print(std::ostream& Os) const;
};
}

#endif
