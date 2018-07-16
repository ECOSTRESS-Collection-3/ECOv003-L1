#include "ecostress_orbit.h"
#include "ecostress_serialize_support.h"
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressOrbit::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(HdfOrbit_Eci_TimeJ2000)
    & GEOCAL_NVP_(large_gap)
    & GEOCAL_NVP_(pad);
}

ECOSTRESS_IMPLEMENT(EcostressOrbit);

/// See base class for description
void EcostressOrbit::print(std::ostream& Os) const
{
  Os << "EcostressOrbit\n"
     << "  File name:        " << file_name() << "\n"
     << "  Min time:         " << min_time() << "\n"
     << "  Max time:         " << max_time() << "\n"
     << "  Large gap:        " << large_gap() << " s\n"
     << "  Extrapolation pad: " << extrapolation_pad() << " s\n";
}



