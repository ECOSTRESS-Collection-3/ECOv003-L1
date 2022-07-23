#include "ecostress_scan_mirror.h"
#include "ecostress_serialize_support.h"
#include "geocal/covariance.h"
#include "geocal/statistic.h"
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressScanMirror::save(Archive& Ar, const unsigned int version) const
{
  // Nothing more to do
}

template<class Archive>
void EcostressScanMirror::load(Archive& Ar, const unsigned int version)
{
  inst_to_sc_nd_ = value(inst_to_sc_);
  camera_to_mirror_nd_ = value(camera_to_mirror_);
  camera_to_mirror_2_nd_ = value(camera_to_mirror_2_);
}


template<class Archive>
void EcostressScanMirror::serialize(Archive & ar, const unsigned int version)
{
  if(version < 1)
    throw GeoCal::Exception("We can't read the older version of EcostressScanMirror, it changed too much. Version must be >=1");
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(WithParameter)
    & GEOCAL_NVP_(evalue)
    & GEOCAL_NVP_(max_encoder_value) & GEOCAL_NVP_(ev0)
    & GEOCAL_NVP_(ev0_2)
    & GEOCAL_NVP_(ang_per_ev)
    & GEOCAL_NVP_(ang_per_ev_2)
    & GEOCAL_NVP_(parameter_mask)
    & GEOCAL_NVP_(inst_to_sc);
  if(version >= 2) {
    ar & GEOCAL_NVP_(camera_to_mirror)
      & GEOCAL_NVP_(camera_to_mirror_2);
  }
  if(version >= 3) {
    ar & GEOCAL_NVP_(boresight_x_offset)
      & GEOCAL_NVP_(boresight_y_offset);
  }
  boost::serialization::split_member(ar, *this, version);
}

ECOSTRESS_IMPLEMENT(EcostressScanMirror);

//-------------------------------------------------------------------------
/// Constructor. The scan angles are in degrees (seems more convenient
/// than the normal radians we use for angles).
///  
/// This uses the data to generate encoder values, useful for
/// simulations.
///
/// Note that the default values here match the test data
/// found in ecostress-test-data
//-------------------------------------------------------------------------

EcostressScanMirror::EcostressScanMirror
(double Scan_start,
 double Scan_end,
 int Number_sample,
 int Number_scan,
 int Max_encoder_value,
 double First_encoder_value_at_0,
 double Second_encoder_value_at_0,
 double Epsilon,
 double Beta,
 double Delta,
 double First_angle_per_ev,
 double Second_angle_per_ev,
 double Yaw,
 double Roll,
 double Pitch,
 double Yaw_2,
 double Roll_2,
 double Pitch_2,
 double Boresight_x_offset,
 double Boresight_y_offset
)
  : evalue_(Number_scan, Number_sample),
    max_encoder_value_(Max_encoder_value),
    ev0_(First_encoder_value_at_0),
    ev0_2_(Second_encoder_value_at_0),
    ang_per_ev_(First_angle_per_ev),
    ang_per_ev_2_(Second_angle_per_ev),
    parameter_mask_(15),
    boresight_x_offset_(Boresight_x_offset),
    boresight_y_offset_(Boresight_y_offset)    
{
  for(int i = 0; i < evalue_.rows(); ++i)
    for(int j = 0; j < evalue_.cols(); ++j) {
      double a = Scan_start +
	(Scan_end - Scan_start) / (evalue_.cols() - 1) * j;
      evalue_(i, j) = angle_to_encoder_value(a, i % 2);
    }
  parameter_mask_ = false;
  blitz::Array<double, 1> t(3);
  t = Epsilon, Beta, Delta;
  euler(t);
  blitz::Array<double, 1> t2(6);
  t2 = Yaw, Pitch, Roll, Yaw_2, Pitch_2, Roll_2;
  mirror_ypr(t2);
}

//-------------------------------------------------------------------------
/// Constructor, taking the encoder values. We fill in bad data values.
//-------------------------------------------------------------------------

EcostressScanMirror::EcostressScanMirror
(const blitz::Array<int, 2>& Encoder_value,
 int Max_encoder_value,
 double First_encoder_value_at_0,
 double Second_encoder_value_at_0,
 double Epsilon,
 double Beta,
 double Delta,
 double First_angle_per_ev,
 double Second_angle_per_ev,
 double Yaw,
 double Roll,
 double Pitch,
 double Yaw_2,
 double Roll_2,
 double Pitch_2,
 double Boresight_x_offset,
 double Boresight_y_offset
 )
  : evalue_(Encoder_value.copy()),
    max_encoder_value_(Max_encoder_value),
    ev0_(First_encoder_value_at_0),
    ev0_2_(Second_encoder_value_at_0),
    ang_per_ev_(First_angle_per_ev),
    ang_per_ev_2_(Second_angle_per_ev),
    parameter_mask_(15),
    boresight_x_offset_(Boresight_x_offset),
    boresight_y_offset_(Boresight_y_offset)    
{
  blitz::Range ra = blitz::Range::all();
  // Look for scans with some missing data, and fill in. We make sure
  // we have at least a handful of good points, we treat this as
  // completely missing to there is too much missing data
  for(int i = 0; i < evalue_.rows(); ++i) {
    if(count(evalue_(i, ra) < 0) > 0 &&
       count(evalue_(i, ra) >= 0) >=
       MIN_GOOD_DATA_FOR_REGRESSION)
      fill_in_scan(i);
  }
  // If one of the first two scans are missing, look forward to the
  // first scan on the same side of the mirror and fill in data. If
  // we don't find any data, give up - we have huge amounts of missing
  // data and can't really do anything with it.
  for(int i = 0; i < 2; ++i) {
    if(count(evalue_(i, ra) < 0) > 0) {
      bool filled = false;
      for(int j = i + 2; j < evalue_.rows(); j+=2) { // +=2 to stay on
						     // same side of mirror
	if(!filled && count(evalue_(j, ra) >= 0) > 0) {
	  evalue_(i, ra) = evalue_(j,ra);
	  filled = true;
	}
      }
      if(!filled)
	throw Exception("We can't find a single scan index without fill values for the encoder values. Too little good data to continue processing.");
    }
  }
  // Look for scans after the first 2 sides of the mirror that are
  // completely missing. For those, we use the previous row for the
  // same side of the mirror.
  for(int i = 2; i < evalue_.rows(); ++i) {
    if(count(evalue_(i, ra) < 0) > 0)
      evalue_(i, ra) = evalue_(i-2,ra); // -2 to stay on same side of mirror.
  }
  parameter_mask_ = false;
  blitz::Array<double, 1> t(3);
  t = Epsilon, Beta, Delta;
  euler(t);
  blitz::Array<double, 1> t2(6);
  t2 = Yaw, Pitch, Roll, Yaw_2, Pitch_2, Roll_2;
  mirror_ypr(t2);
}

//-------------------------------------------------------------------------
/// Fill in missing data for a scan index, pulled out into its own subroutine
/// just to make this cleaner. We just do a linear regression against
/// the data found in the row
//-------------------------------------------------------------------------

void EcostressScanMirror::fill_in_scan(int S)
{
  // Do a linear regression against the data.
  Covariance cov;
  Statistic x_stat;
  for(int i = 0; i < evalue_.cols(); ++i)
    if(evalue_(S,i) >= 0) {
      cov.add(i, evalue_(S,i));
      x_stat.add(i);
    }
  double b = cov.covariance() / (x_stat.sigma() * x_stat.sigma());
  double a = cov.mean2() - cov.mean1() * b;
  // Now, fill in data with linear regression
  for(int i = 0; i < evalue_.cols(); ++i)
    if(evalue_(S,i) < 0)
      evalue_(S, i) = a + b * i;
}

void EcostressScanMirror::print(std::ostream& Os) const
{
  Os << "EcostressScanMirror:\n"
     << "  Number samples:                  " << number_sample() << "\n"
     << "  Number scan:                     " << number_scan() << "\n"
     << "  Max encoder value:               " << max_encoder_value_ << "\n"
     << "  First encoder value at 0:        " << ev0_ << "\n"
     << "  Second encoder value at 0:       " << ev0_2_ << "\n"
     << "  First angler per encoder value:  " << ang_per_ev_ << "\n"
     << "  Second angler per encoder value: " << ang_per_ev_2_ << "\n"
     << "  Instrument to spacecraft:        " << instrument_to_sc() << "\n"
     << "  Camera to mirror:                " << camera_to_mirror_nd_ << "\n"
     << "  Camera to mirror side 2:         " << camera_to_mirror_2_nd_ << "\n"
     << "  Boresight X offset:              " << boresight_x_offset() << "\n"
     << "  Boresight Y offset:              " << boresight_y_offset() << "\n";
}

//-----------------------------------------------------------------------
/// Set parameter. Right now this is Euler epsilon, beta, delta,
/// first_encoder_value_at_0, second_encoder_value_at_0,
/// first_angle_per_encoder_value, second_angle_per_encoder_value.
//-----------------------------------------------------------------------

void EcostressScanMirror::parameter(const blitz::Array<double, 1>& Parm)
{
  if(Parm.rows() != 15)
    throw Exception("Wrong sized parameter passed.");
  // euler calls notify_update(), so we don't need to do that.
  euler(Parm(blitz::Range(0,2)));
  mirror_ypr(Parm(blitz::Range(3,8)));
  ev0_ = Parm(9);
  ev0_2_ = Parm(10);
  ang_per_ev_ = Parm(11);
  ang_per_ev_2_ = Parm(12);
  boresight_x_offset_ = Parm(13);
  boresight_y_offset_ = Parm(14);
}

void EcostressScanMirror::parameter_with_derivative(const GeoCal::ArrayAd<double, 1>& Parm)
{
  if(Parm.rows() != 15)
    throw Exception("Wrong sized parameter passed.");
  // euler calls notify_update(), so we don't need to do that.
  euler_with_derivative(Parm(blitz::Range(0,2)));
  mirror_ypr_with_derivative(Parm(blitz::Range(3,8)));
  ev0_ = Parm(9);
  ev0_2_ = Parm(10);
  ang_per_ev_ = Parm(11);
  ang_per_ev_2_ = Parm(12);
  boresight_x_offset_ = Parm(13);
  boresight_y_offset_ = Parm(14);
}

blitz::Array<double, 1> EcostressScanMirror::parameter() const
{
  blitz::Array<double, 1> res(15);
  res(blitz::Range(0,2)) = euler();
  res(blitz::Range(3,8)) = mirror_ypr();
  res(9) = first_encoder_value_at_0();
  res(10) = second_encoder_value_at_0();
  res(11) = first_angle_per_encoder_value();
  res(12) = second_angle_per_encoder_value();
  res(13) = boresight_x_offset_.value();
  res(14) = boresight_y_offset_.value();
  return res;
}

GeoCal::ArrayAd<double, 1> EcostressScanMirror::parameter_with_derivative() const
{
  blitz::Array<AutoDerivative<double>, 1> res(15);
  res(blitz::Range(0,2)) = euler_with_derivative();
  res(blitz::Range(3,8)) = mirror_ypr_with_derivative();
  res(9) = first_encoder_value_at_0_with_derivative();
  res(10) = second_encoder_value_at_0_with_derivative();
  res(11) = first_angle_per_encoder_value_with_derivative();
  res(12) = second_angle_per_encoder_value_with_derivative();
  res(13) = boresight_x_offset_;
  res(14) = boresight_y_offset_;
  return ArrayAd<double, 1>(res);
}

std::vector<std::string> EcostressScanMirror::parameter_name() const
{
  std::vector<std::string> res;
  res.push_back("Instrument Euler Epsilon");
  res.push_back("Instrument Euler Beta");
  res.push_back("Instrument Euler Delta");
  res.push_back("Camera to Mirror Yaw");
  res.push_back("Camera to Mirror Pitch");
  res.push_back("Camera to Mirror Roll");
  res.push_back("Camera to Mirror Side 2 Yaw");
  res.push_back("Camera to Mirror Side 2 Pitch");
  res.push_back("Camera to Mirror Side 2 Roll");
  res.push_back("First encoder value at 0");
  res.push_back("Second encoder value at 0");
  res.push_back("First angle per encoder value");
  res.push_back("Second angle per encoder value");
  res.push_back("Boresight X offset");
  res.push_back("Boresight Y offset");
  return res;
}



  
