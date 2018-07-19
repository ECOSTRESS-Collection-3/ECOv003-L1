#ifndef ECOSTRESS_CAMERA_H
#define ECOSTRESS_CAMERA_H
#include "geocal/quaternion_camera.h"
#include "ecostress_paraxial_transform.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress camera model.

  Right now we model the optical nonlinearity with 
  EcostressParaxialTransform. 

  Note that to match the field angles from our FPA distortion spread
  sheet we need to add a scale and offset to the DCS yf value. Not
  sure what the physical source of this, the CCD may be at an angle
  relative to the optics, or the optics may be different in X vs. Y
  direction. In any case, we want to match the actual field angles.
*******************************************************************/

class EcostressCamera : public GeoCal::QuaternionCamera {
public:
  EcostressCamera(double Focal_length = 427.6, double Y_scale = 1.0,
		  double Y_offset = 0,
		  boost::math::quaternion<double> Frame_to_sc_q =
		  boost::math::quaternion<double>(1,0,0,0));
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
  double y_scale() const {return y_scale_;}
  void y_scale(double V) { y_scale_ = V;}
  double y_offset() const {return y_offset_;}
  void y_offset(double V) { y_offset_ = V;}
private:
  boost::shared_ptr<EcostressParaxialTransform> paraxial_transform_;
  double y_scale_, y_offset_;
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressCamera);
BOOST_CLASS_VERSION(Ecostress::EcostressCamera, 1)
#endif
