#include "combine_orbit.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void CombineOrbit::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(Orbit)
    & GEOCAL_NVP_(orb_list);
}

ECOSTRESS_IMPLEMENT(CombineOrbit);

/// See base class for description
void CombineOrbit::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "CombineOrbit\n";
  for(auto i : orb_list_)
    opad << *i << "\n";
}

/// See base class for description
boost::shared_ptr<OrbitData> CombineOrbit::orbit_data(Time T) const
{
  for(auto i : orb_list_)
    if(T >= i->min_time() && T < i->max_time())
      return i->orbit_data(T);
  GeoCal::Exception e;
  e << "Time " << T << "not found in orbit list";
  throw e;
}

boost::shared_ptr<GeoCal::OrbitData> 
CombineOrbit::orbit_data(const GeoCal::TimeWithDerivative& T) const
{
  for(auto i : orb_list_)
    if(T >= i->min_time() && T < i->max_time())
      return i->orbit_data(T);
  GeoCal::Exception e;
  e << "Time " << T << "not found in orbit list";
  throw e;
}

