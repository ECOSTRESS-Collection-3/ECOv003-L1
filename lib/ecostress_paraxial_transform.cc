#include "ecostress_paraxial_transform.h"
#include "geocal/geocal_serialize_support.h"

using namespace Ecostress;

template<class Archive>
void EcostressParaxialTransform::serialize(Archive & ar, const unsigned int version)
{
  boost::serialization::void_cast_register<EcostressParaxialTransform,
					   GeoCal::GenericObject>();
  ar & GEOCAL_NVP_(paraxial_to_real)
    & GEOCAL_NVP_(real_to_paraxial);
}

BOOST_CLASS_EXPORT_IMPLEMENT(Ecostress::EcostressParaxialTransform);
