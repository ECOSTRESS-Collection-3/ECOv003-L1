#ifndef ECOSTRESS_SCAN_MIRROR_H
#define ECOSTRESS_SCAN_MIRROR_H
#include "geocal/printable.h"
#include "geocal/image_coordinate.h"
#include "geocal/geocal_quaternion.h"
#include "geocal/geocal_autoderivative_quaternion.h"
#include "geocal/constant.h"
#include "geocal/observer.h"
#include "geocal/with_parameter.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress scan mirror.

  Because it is a convenient place, we also include the ecostress
  instrument to spacecraft coordinate transformation (i.e., the
  alignment of the instrument with the ISS which is nominally an
  identity transformation).

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

class EcostressScanMirror: public GeoCal::Printable<EcostressScanMirror>,
			   public GeoCal::Observable<EcostressScanMirror>,
			   public GeoCal::WithParameter {
public:
  enum { MIN_GOOD_DATA_FOR_REGRESSION = 10 };
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
  virtual ~EcostressScanMirror() {}

  virtual void add_observer(GeoCal::Observer<EcostressScanMirror>& Obs) 
  { add_observer_do(Obs, *this);}
  virtual void remove_observer(GeoCal::Observer<EcostressScanMirror>& Obs) 
  { remove_observer_do(Obs, *this);}

  virtual blitz::Array<double, 1> parameter() const;
  virtual void parameter(const blitz::Array<double, 1>& Parm);
  virtual GeoCal::ArrayAd<double, 1> parameter_with_derivative() const;
  virtual void parameter_with_derivative
  (const GeoCal::ArrayAd<double, 1>& Parm);
  virtual std::vector<std::string> parameter_name() const;

//-----------------------------------------------------------------------
/// Return the parameter subset mask, where "true" means include the
/// parameter and "false" means don't.
//-----------------------------------------------------------------------

  virtual blitz::Array<bool, 1> parameter_mask() const 
  { return parameter_mask_; }

//-----------------------------------------------------------------------
/// Indicate if we fit for instrument euler epsilon.
//-----------------------------------------------------------------------

  bool fit_epsilon() const { return parameter_mask_(0); }
  void fit_epsilon(bool V) {parameter_mask_(0) = V;}

//-----------------------------------------------------------------------
/// Indicate if we fit for instrument euler beta.
//-----------------------------------------------------------------------

  bool fit_beta() const { return parameter_mask_(1); }
  void fit_beta(bool V) {parameter_mask_(1) = V;}

//-----------------------------------------------------------------------
/// Indicate if we fit for instrument euler delta.
//-----------------------------------------------------------------------

  bool fit_delta() const { return parameter_mask_(2); }
  void fit_delta(bool V) {parameter_mask_(2) = V;}

//-----------------------------------------------------------------------
/// Indicate if we fit for first encoder value at 0
//-----------------------------------------------------------------------

  bool fit_first_encoder_value_at_0() const { return parameter_mask_(3); }
  void fit_first_encoder_value_at_0(bool V) {parameter_mask_(3) = V;}

//-----------------------------------------------------------------------
/// Indicate if we fit for second encoder value at 0
//-----------------------------------------------------------------------

  bool fit_second_encoder_value_at_0() const { return parameter_mask_(4); }
  void fit_second_encoder_value_at_0(bool V) {parameter_mask_(4) = V;}
  
//-----------------------------------------------------------------------
/// Indicate if we fit for first angle per encoder value
//-----------------------------------------------------------------------

  bool fit_first_angle_per_encoder_value() const { return parameter_mask_(5); }
  void fit_first_angle_per_encoder_value(bool V) {parameter_mask_(5) = V;}

//-----------------------------------------------------------------------
/// Indicate if we fit for second angle per encoder value
//-----------------------------------------------------------------------

  bool fit_second_angle_per_encoder_value() const { return parameter_mask_(6); }
  void fit_second_angle_per_encoder_value(bool V) {parameter_mask_(6) = V;}
  
//-------------------------------------------------------------------------
/// Angle encoder values.
//-------------------------------------------------------------------------

  const blitz::Array<int, 2>& encoder_value() const {return evalue_;}

//-----------------------------------------------------------------------
/// Return the equivalent Euler angles epsilon, beta, delta for the
/// frame_to_sc. These are in radians.
//-----------------------------------------------------------------------

  blitz::Array<double, 1> euler() const
  {
    blitz::Array<double, 1> res(3);
    GeoCal::quat_to_euler(instrument_to_sc(), res(0), res(1), res(2));
    return res;
  }

//-----------------------------------------------------------------------
/// Return the equivalent Euler angles epsilon, beta, delta for the
/// frame_to_sc. These are in radians.
//-----------------------------------------------------------------------

  blitz::Array<GeoCal::AutoDerivative<double>, 1> euler_with_derivative() const
  {
    blitz::Array<GeoCal::AutoDerivative<double>, 1> res(3);
    GeoCal::quat_to_euler(instrument_to_sc_with_derivative(),
			  res(0), res(1), res(2));
    return res;
  }

//-----------------------------------------------------------------------
/// Update the instrument_to_sc using the given Euler angles epsilon, beta,
/// data in radians.
//-----------------------------------------------------------------------

  void euler(const blitz::Array<double, 1>& Euler)
  {
    if(Euler.rows() != 3)
      throw GeoCal::Exception("Ypr must be size 3");
    instrument_to_sc(GeoCal::quat_rot("zyx", Euler(0), Euler(1), Euler(2)));
  }

//-----------------------------------------------------------------------
/// Update the frame_to_sc using the given Euler angles epsilon, beta,
/// data in radians.
//-----------------------------------------------------------------------

  void euler_with_derivative(const blitz::Array<GeoCal::AutoDerivative<double>, 1>& Euler)
  {
    if(Euler.rows() != 3)
      throw GeoCal::Exception("Euler must be size 3");
    instrument_to_sc_with_derivative(GeoCal::quat_rot("zyx", Euler(0), Euler(1), Euler(2)));
    notify_update();
  }

  void euler_with_derivative(const GeoCal::ArrayAd<double, 1>& Euler)
  {
    if(Euler.rows() != 3)
      throw GeoCal::Exception("Euler must be size 3");
    instrument_to_sc_with_derivative(GeoCal::quat_rot("zyx", Euler(0), Euler(1), Euler(2)));
    notify_update();
  }

//-----------------------------------------------------------------------
/// Instrument to spacecraft quaternion.
//-----------------------------------------------------------------------

  boost::math::quaternion<double> instrument_to_sc() const
  {return inst_to_sc_nd_;}

//-----------------------------------------------------------------------
/// Instrument to spacecraft quaternion.
//-----------------------------------------------------------------------

  boost::math::quaternion<GeoCal::AutoDerivative<double> > 
  instrument_to_sc_with_derivative() const
  {return inst_to_sc_;}

//-----------------------------------------------------------------------
/// Set instrument to spacecraft quaternion.
//-----------------------------------------------------------------------

  void instrument_to_sc(const boost::math::quaternion<double>& inst_to_sc_q) 
  {
    inst_to_sc_ = GeoCal::to_autoderivative(inst_to_sc_q);
    inst_to_sc_nd_ = inst_to_sc_q;
    notify_update();
  }


//-----------------------------------------------------------------------
/// Set instrument to spacecraft quaternion.
//-----------------------------------------------------------------------

  void instrument_to_sc_with_derivative(const boost::math::quaternion<GeoCal::AutoDerivative<double> >& inst_to_sc_q) 
  { inst_to_sc_ = inst_to_sc_q;
    inst_to_sc_nd_ = value(inst_to_sc_);
    notify_update(); }

  
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

  double first_angle_per_encoder_value() const
  { return ang_per_ev_.value(); }
  GeoCal::AutoDerivative<double> first_angle_per_encoder_value_with_derivative() const
  { return ang_per_ev_; }

  double second_angle_per_encoder_value() const
  { return ang_per_ev_2_.value(); }
  GeoCal::AutoDerivative<double> second_angle_per_encoder_value_with_derivative() const
  { return ang_per_ev_2_; }
  
//-------------------------------------------------------------------------
/// Encoder value at 0 angle. This is for the first side of the mirror.
//-------------------------------------------------------------------------

  double first_encoder_value_at_0() const { return ev0_.value(); }
  GeoCal::AutoDerivative<double> first_encoder_value_at_0_with_derivative() const { return ev0_; }

//-------------------------------------------------------------------------
/// Encoder value at 0 angle. This is for the second side of the mirror.
//-------------------------------------------------------------------------

  double second_encoder_value_at_0() const { return ev0_2_.value(); }
  GeoCal::AutoDerivative<double> second_encoder_value_at_0_with_derivative() const { return ev0_2_; }

//-------------------------------------------------------------------------
/// Calculate angle for a given encoder value.
//-------------------------------------------------------------------------

  double angle_from_encoder_value(double Evalue) const
  {
    return (Evalue < (max_encoder_value() / 2) ?
	    (Evalue - first_encoder_value_at_0()) *
	    first_angle_per_encoder_value() :
	    (Evalue - second_encoder_value_at_0()) *
	    second_angle_per_encoder_value());
  }
  GeoCal::AutoDerivative<double> angle_from_encoder_value
  (const GeoCal::AutoDerivative<double>& Evalue) const
  {
    return (Evalue.value() < (max_encoder_value() / 2) ?
	    (Evalue - first_encoder_value_at_0_with_derivative()) *
	    first_angle_per_encoder_value_with_derivative():
	    (Evalue - second_encoder_value_at_0_with_derivative()) *
	    second_angle_per_encoder_value_with_derivative());
  }

//-------------------------------------------------------------------------
/// Calculate encoder value from angle and mirror side (0 or 1).
//-------------------------------------------------------------------------

  int angle_to_encoder_value(double Angle_deg, int Mirror_side) const
  {
    return (int) floor(Angle_deg / (Mirror_side == 0 ?
				    first_angle_per_encoder_value():
				    second_angle_per_encoder_value()) + 0.5) +
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
  { return instrument_to_sc() *
      GeoCal::quat_rot_x(scan_mirror_angle(Scan_index, Ic_sample) *
			 GeoCal::Constant::deg_to_rad); }
  boost::math::quaternion<GeoCal::AutoDerivative<double> >
  rotation_quaternion(int Scan_index,
		     const GeoCal::AutoDerivative<double>& Ic_sample) const
  { return instrument_to_sc_with_derivative() *
      GeoCal::quat_rot_x(scan_mirror_angle(Scan_index, Ic_sample) *
			 GeoCal::Constant::deg_to_rad); }
  virtual void print(std::ostream& Os) const;
private:
  blitz::Array<int, 2> evalue_;
  int max_encoder_value_;
  GeoCal::AutoDerivative<double> ev0_, ev0_2_;
  GeoCal::AutoDerivative<double> ang_per_ev_, ang_per_ev_2_;
  blitz::Array<bool, 1> parameter_mask_;
				// Mask of parameters we are fitting for.
  // ** Important, see note below about inst_to_sc_nd_. You can
  // use the member function inst_to_sc(val) to set both at the same
  // time if you like ***
  boost::math::quaternion<GeoCal::AutoDerivative<double> > inst_to_sc_;
  // Turns out that converting inst_to_sc_ to a version without
  // derivatives is a bit of a bottle neck in some calculations (e.g.,
  // Ipi). So we keep a copy of value(inst_to_sc_) so we don't need
  // to calculate it multiple times.
  boost::math::quaternion<double> inst_to_sc_nd_;
  void fill_in_scan(int S);
  virtual void notify_update()
  {
    notify_update_do(*this);
  }
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  template<class Archive>
  void save(Archive& Ar, const unsigned int version) const;
  template<class Archive>
  void load(Archive& Ar, const unsigned int version);
};

}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressScanMirror);
BOOST_CLASS_VERSION(Ecostress::EcostressScanMirror, 1)
#endif
  
  
