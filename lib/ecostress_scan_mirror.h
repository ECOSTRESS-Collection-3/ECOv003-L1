#ifndef ECOSTRESS_SCAN_MIRROR_H
#define ECOSTRESS_SCAN_MIRROR_H
#include "geocal/printable.h"
#include "geocal/image_coordinate.h"
#include "geocal/geocal_quaternion.h"
#include "geocal/constant.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress can mirror.

  Note that we have independent values for encoder_value_at_0, one for
  each side of the scan mirror. We would expect this to be exactly 1/2
  the maximum encoder value, but for reasons not understood this
  doesn't appear to be the case.

  From Colin: You may recall we had an issue with the target being
  about 5 pixels offset from the start of of an acquisition depending
  on which side of the mirror we were on.  I then added a
  (configurable) 120 encoder start offset on one side of the mirror
  which is pretty close to the gap you see in the data.  We are not
  completely sure why we see this gap, I believe the expectation was
  we would have to do some calibration once in flight to make sure
  things line up.

  We'll allow each side of the mirror to have an independent EV_0. If
  we end up not having a gap, we can then just set the second EV_0 to
  first EV_0 + maximum encoder value / 2, but if there is an offset
  we can account for it.
*******************************************************************/

class EcostressScanMirror: public GeoCal::Printable<EcostressScanMirror> {
public:
  enum { MIN_GOOD_DATA_FOR_REGRESSION = 10 };
  EcostressScanMirror(double Scan_start = -26.488105667851173,
		      double Scan_end = 26.488105667851173,
		      int Number_sample = 5400,
		      int Number_scan = 44,
		      int Max_encoder_value = 1749248,
		      int First_encoder_value_at_0 = 401443,
		      int Second_encoder_value_at_0 = 1275903
		      );
  EcostressScanMirror(const blitz::Array<int, 2>& Encoder_value,
		      int Max_encoder_value = 1749248,
		      int First_encoder_value_at_0 = 401443,
		      int Second_encoder_value_at_0 = 1275903
		      );
  virtual ~EcostressScanMirror() {}

//-------------------------------------------------------------------------
/// Angle encoder values.
//-------------------------------------------------------------------------

  const blitz::Array<int, 2>& encoder_value() const {return evalue_;}

//-------------------------------------------------------------------------
/// Number of samples in scan mirror.
//-------------------------------------------------------------------------

  int number_sample() const { return evalue_.cols(); }

//-------------------------------------------------------------------------
/// Number of scans in scan mirror.
//-------------------------------------------------------------------------

  int number_scan() const { return evalue_.rows(); }
  
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

  int first_encoder_value_at_0() const { return ev0_; }

//-------------------------------------------------------------------------
/// Encoder value at 0 angle. This is for the second side of the mirror.
//-------------------------------------------------------------------------

  int second_encoder_value_at_0() const { return ev0_2_; }

//-------------------------------------------------------------------------
/// Calculate angle for a given encoder value.
//-------------------------------------------------------------------------

  double angle_from_encoder_value(double Evalue) const
  {
    return (Evalue < (max_encoder_value() / 2) ?
	    Evalue - first_encoder_value_at_0() :
	    Evalue - second_encoder_value_at_0()) *
      angle_per_encoder_value();
  }
  GeoCal::AutoDerivative<double> angle_from_encoder_value
  (const GeoCal::AutoDerivative<double>& Evalue) const
  {
    return (Evalue.value() < (max_encoder_value() / 2) ?
	    Evalue - first_encoder_value_at_0() :
	    Evalue - second_encoder_value_at_0()) *
      angle_per_encoder_value();
  }

//-------------------------------------------------------------------------
/// Calculate encoder value from angle and mirror side (0 or 1).
//-------------------------------------------------------------------------

  int angle_to_encoder_value(double Angle_deg, int Mirror_side) const
  {
    return (int) floor(Angle_deg / angle_per_encoder_value() + 0.5) +
      (Mirror_side == 0 ? first_encoder_value_at_0() :
       second_encoder_value_at_0());
  }

//-------------------------------------------------------------------------
/// Determine EV from Scan_index and Ic_sample,
/// interpolating/extrapolating if needed.
//-------------------------------------------------------------------------

  double encoder_value_interpolate(int Scan_index, double Ic_sample) const
  {
    range_check(Scan_index, 0, evalue_.rows());
    int i = (int) floor(Ic_sample + 0.5);
    if(i < 0)
      i = 0;
    if(i > evalue_.cols() - 2)
      i = evalue_.cols() - 2;
    double v1 = evalue_(Scan_index, i);
    double v2 = evalue_(Scan_index, i+1);
    return v1 + (v2 - v1) * (Ic_sample - i);
  }
  GeoCal::AutoDerivative<double>
  encoder_value_interpolate(int Scan_index,
    const GeoCal::AutoDerivative<double> Ic_sample) const
  {
    range_check(Scan_index, 0, evalue_.rows());
    int i = (int) floor(Ic_sample.value() + 0.5);
    if(i < 0)
      i = 0;
    if(i > evalue_.cols() - 2)
      i = evalue_.cols() - 2;
    double v1 = evalue_(Scan_index, i);
    double v2 = evalue_(Scan_index, i+1);
    return v1 + (v2 - v1) * (Ic_sample - i);
  }

//-------------------------------------------------------------------------
/// Scan mirror angle, in degrees.
//-------------------------------------------------------------------------

  double scan_mirror_angle(int Scan_index, double Ic_sample) const
  { return angle_from_encoder_value(encoder_value_interpolate(Scan_index, Ic_sample));}

  GeoCal::AutoDerivative<double> scan_mirror_angle
  (int Scan_index, const GeoCal::AutoDerivative<double>& Ic_sample) const
  { return angle_from_encoder_value(encoder_value_interpolate(Scan_index, Ic_sample));}
  
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
  blitz::Array<int, 2> evalue_;
  int max_encoder_value_, ev0_, ev0_2_;
  void fill_in_scan(int S);
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};

}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressScanMirror);
#endif
  
  
