#ifndef ECOSTRESS_CAMERA_H
#define ECOSTRESS_CAMERA_H
#include "geocal/quaternion_camera.h"
#include "ecostress_paraxial_transform.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress camera model.

  Right now we model the optical nonlinearity with 
  EcostressParaxialTransform. This is likely just a place holder that
  will get replaced with something different when we have the real
  camera model.
*******************************************************************/

class EcostressCamera : public GeoCal::QuaternionCamera {
public:
  EcostressCamera();
  virtual ~EcostressCamera() {}
  virtual void print(std::ostream& Os) const;
  const boost::shared_ptr<EcostressParaxialTransform>& paraxial_transform()
    const { return paraxial_transform_; }
  void paraxial_transform(const boost::shared_ptr<EcostressParaxialTransform>& v)
  { paraxial_transform_ = v; }
  virtual void dcs_to_focal_plane(int Band,
				  const boost::math::quaternion<double>& Dcs,
				  double& Xfp, double& Yfp) const;
  virtual void dcs_to_focal_plane
  (int Band,
   const boost::math::quaternion<GeoCal::AutoDerivative<double> >& Dcs,
   GeoCal::AutoDerivative<double>& Xfp, 
   GeoCal::AutoDerivative<double>& Yfp) const;
  virtual boost::math::quaternion<double> 
  focal_plane_to_dcs(int Band, double Xfp, double Yfp) const;
  virtual boost::math::quaternion<GeoCal::AutoDerivative<double> > 
  focal_plane_to_dcs(int Band, const GeoCal::AutoDerivative<double>& Xfp, 
		     const GeoCal::AutoDerivative<double>& Yfp) const;
  /// Convenience function to mask all the parameters we can fit for.
  void mask_all_parameter() { parameter_mask_ = false; }
private:
  boost::shared_ptr<EcostressParaxialTransform> paraxial_transform_;
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressCamera);
#endif
