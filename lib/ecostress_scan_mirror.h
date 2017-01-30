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
		      int Number_sample = 5400)
    : scan_start_(Scan_start), scan_end_(Scan_end),
      number_sample_(Number_sample)
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
/// Scan mirror angle, in degrees.
//-------------------------------------------------------------------------

  double scan_mirror_angle(double Ic_sample) const
  { return scan_start_ + Ic_sample * scan_step_; }

//-------------------------------------------------------------------------
/// Rotation matrix that take the view vector for the Camera and takes
/// it to the space craft coordinate system.
//-------------------------------------------------------------------------

  boost::math::quaternion<double>
  rotation_quaterion(double Ic_sample) const
  { return GeoCal::quat_rot_x(scan_mirror_angle(Ic_sample) *
			      GeoCal::Constant::deg_to_rad); }
  virtual void print(std::ostream& Os) const;
private:
  double scan_start_, scan_end_, scan_step_;
  int number_sample_;
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
  
  
