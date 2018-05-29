#include "ecostress_scan_mirror.h"
#include "ecostress_serialize_support.h"
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


void EcostressScanMirror::print(std::ostream& Os) const
{
  Os << "EcostressScanMirror:\n"
     << "  Number samples:            " << number_sample() << "\n"
     << "  Number scan:               " << number_scan() << "\n"
     << "  Max encoder value:         " << max_encoder_value_ << "\n"
     << "  First encoder value at 0:  " << ev0_ << "\n"
     << "  Second encoder value at 0: " << ev0_2_ << "\n";
}




  
