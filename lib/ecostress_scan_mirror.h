#ifndef ECOSTRESS_SCAN_MIRROR_H
#define ECOSTRESS_SCAN_MIRROR_H
#include "geocal/printable.h"
#include "geocal/image_coordinate.h"
#include "geocal/geocal_quaternion.h"
#include "geocal/constant.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress can mirror.

  I'm not real sure about the interface for this, we may change this
  over time. But this is the initial version of this.
*******************************************************************/

class EcostressScanMirror: public GeoCal::Printable<EcostressScanMirror> {
public:
//-------------------------------------------------------------------------
/// Constructor. The scan angles are in degrees (seems more convenient
/// than the normal radians we use for angles).
//-------------------------------------------------------------------------

  EcostressScanMirror(double Scan_start = -25.5, double Scan_end = 25.5,
		      int Number_sample = 5400,
		      int Max_encoder_value = 1749248,
		      int Encoder_value_at_0 = 401443)
    : scan_start_(Scan_start), scan_end_(Scan_end),
      number_sample_(Number_sample), max_encoder_value_(Max_encoder_value),
      ev0_(Encoder_value_at_0)
  { init(); }

//-------------------------------------------------------------------------
/// Scan start in degrees.
//-------------------------------------------------------------------------

  double scan_start() const {return scan_start_;}
  
//-------------------------------------------------------------------------
/// Scan end in degrees.
//-------------------------------------------------------------------------

  double scan_end() const {return scan_end_;}

//-------------------------------------------------------------------------
/// Number sample
//-------------------------------------------------------------------------

  int number_sample() const {return number_sample_;}

//-------------------------------------------------------------------------
/// Maximum encoder value. Note that we go through 2 360 degree
/// rotation because of the set up of the mirrors.
//-------------------------------------------------------------------------

  int max_encoder_value() const {return max_encoder_value_;}

//-------------------------------------------------------------------------
/// Angle that a single encoder value goes through, in degrees.
//-------------------------------------------------------------------------

  double angle_per_encoder_value() const
  { return 360.0 / max_encoder_value() * 2; }

//-------------------------------------------------------------------------
/// Encoder value at 0 angle. This is for the first side of the mirror.
//-------------------------------------------------------------------------

  int encoder_value_at_0() const { return ev0_; }

//-------------------------------------------------------------------------
/// Calculate angle for a given encoder value.
//-------------------------------------------------------------------------

  double angle_from_encoder_value(int Evalue) const
  {
    return (Evalue % (max_encoder_value() / 2) - encoder_value_at_0()) *
      angle_per_encoder_value();
  }
  
//-------------------------------------------------------------------------
/// Scan mirror angle, in degrees.
//-------------------------------------------------------------------------

  double scan_mirror_angle(int Scan_index, double Ic_sample) const
  { return scan_start_ + Ic_sample * scan_step_; }

  GeoCal::AutoDerivative<double> scan_mirror_angle
  (int Scan_index, const GeoCal::AutoDerivative<double>& Ic_sample) const
  { return scan_start_ + Ic_sample * scan_step_; }
  
//-------------------------------------------------------------------------
/// Rotation matrix that take the view vector for the Camera and takes
/// it to the space craft coordinate system.
//-------------------------------------------------------------------------

  boost::math::quaternion<double>
  rotation_quaternion(int Scan_index, double Ic_sample) const
  { return GeoCal::quat_rot_x(scan_mirror_angle(Scan_index, Ic_sample) *
			      GeoCal::Constant::deg_to_rad); }
  boost::math::quaternion<GeoCal::AutoDerivative<double> >
  rotation_quaternion(int Scan_index,
		     const GeoCal::AutoDerivative<double>& Ic_sample) const
  { return GeoCal::quat_rot_x(scan_mirror_angle(Scan_index, Ic_sample) *
			      GeoCal::Constant::deg_to_rad); }
  virtual void print(std::ostream& Os) const;
private:
  double scan_start_, scan_end_, scan_step_;
  int number_sample_;
  int max_encoder_value_, ev0_;
  void init() { scan_step_ = (scan_end_ - scan_start_) / number_sample_; }
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  template<class Archive>
  void save(Archive & ar, const unsigned int version) const;
  template<class Archive>
  void load(Archive & ar, const unsigned int version);
};

}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressScanMirror);
#endif
  
  
