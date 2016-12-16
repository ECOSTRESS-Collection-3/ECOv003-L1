#include "geocal/geocal_serialize_support.h"

#define ECOSTRESS_IMPLEMENT(NAME) \
BOOST_CLASS_EXPORT_IMPLEMENT(Ecostress::NAME); \
template void NAME::serialize(boost::archive::polymorphic_oarchive& ar, \
				    const unsigned int version); \
template void NAME::serialize(boost::archive::polymorphic_iarchive& ar, \
				    const unsigned int version);
#define ECOSTRESS_SPLIT_IMPLEMENT(NAME) \
BOOST_CLASS_EXPORT_IMPLEMENT(Ecostress::NAME); \
template void NAME::save(boost::archive::polymorphic_oarchive& ar, \
				    const unsigned int version) const; \
template void NAME::load(boost::archive::polymorphic_iarchive& ar, \
				    const unsigned int version);

#define ECOSTRESS_BASE(NAME,BASE) boost::serialization::void_cast_register<Ecostress::NAME, Ecostress::BASE>();
#define ECOSTRESS_GENERIC_BASE(NAME) ECOSTRESS_BASE(NAME, GenericObject);
