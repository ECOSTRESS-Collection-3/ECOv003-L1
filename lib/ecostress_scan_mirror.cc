#include "ecostress_scan_mirror.h"
#include "ecostress_serialize_support.h"
#include "geocal/covariance.h"
#include "geocal/statistic.h"
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressScanMirror::serialize(Archive & ar, const unsigned int version)
{
  ECOSTRESS_GENERIC_BASE(EcostressScanMirror);
  ar & GEOCAL_NVP_(evalue)
    & GEOCAL_NVP_(max_encoder_value) & GEOCAL_NVP_(ev0)
    & GEOCAL_NVP_(ev0_2);
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
 int First_encoder_value_at_0,
 int Second_encoder_value_at_0
)
  : evalue_(Number_scan, Number_sample),
    max_encoder_value_(Max_encoder_value),
    ev0_(First_encoder_value_at_0),
    ev0_2_(Second_encoder_value_at_0)
{
  for(int i = 0; i < evalue_.rows(); ++i)
    for(int j = 0; j < evalue_.cols(); ++j) {
      double a = Scan_start +
	(Scan_end - Scan_start) / (evalue_.cols() - 1) * j;
      evalue_(i, j) = angle_to_encoder_value(a, i % 2);
    }
}

//-------------------------------------------------------------------------
/// Constructor, taking the encoder values. We fill in bad data values.
//-------------------------------------------------------------------------

EcostressScanMirror::EcostressScanMirror
(const blitz::Array<int, 2>& Encoder_value,
 int Max_encoder_value,
 int First_encoder_value_at_0,
 int Second_encoder_value_at_0)
  : evalue_(Encoder_value.copy()),
    max_encoder_value_(Max_encoder_value),
    ev0_(First_encoder_value_at_0),
    ev0_2_(Second_encoder_value_at_0)
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
     << "  Number samples:            " << number_sample() << "\n"
     << "  Number scan:               " << number_scan() << "\n"
     << "  Max encoder value:         " << max_encoder_value_ << "\n"
     << "  First encoder value at 0:  " << ev0_ << "\n"
     << "  Second encoder value at 0: " << ev0_2_ << "\n";
}




  
