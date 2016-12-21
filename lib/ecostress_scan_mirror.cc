#include "ecostress_scan_mirror.h"
#include "ecostress_serialize_support.h"
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressScanMirror::save(Archive & ar, const unsigned int version) const
{
  // Nothing more to do
}

template<class Archive>
void EcostressScanMirror::load(Archive & ar, const unsigned int version)
{
  init();
}

template<class Archive>
void EcostressScanMirror::serialize(Archive & ar, const unsigned int version)
{
  ECOSTRESS_GENERIC_BASE(EcostressScanMirror);
  ar & GEOCAL_NVP_(scan_start)
    & GEOCAL_NVP_(scan_end)
    & GEOCAL_NVP_(number_sample);
  boost::serialization::split_member(ar, *this, version);
}

ECOSTRESS_IMPLEMENT(EcostressScanMirror);

void EcostressScanMirror::print(std::ostream& Os) const
{
  Os << "EcostressScanMirror:\n"
     << "  Scan start:     " << scan_start_ << " deg\n"
     << "  Scan end:       " << scan_end_ << " deg\n"
     << "  Number_sample:  " << number_sample_ << "\n";
}




  
