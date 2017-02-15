#include "simulated_radiance.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"

using namespace Ecostress;

template<class Archive>
void SimulatedRadiance::save(Archive & ar, const unsigned int version) const
{
  // Nothing more to do
}

template<class Archive>
void SimulatedRadiance::load(Archive & ar, const unsigned int version)
{
  init();
}

template<class Archive>
void SimulatedRadiance::serialize(Archive & ar, const unsigned int version)
{
  ECOSTRESS_GENERIC_BASE(SimulatedRadiance);
  ar & GEOCAL_NVP_(gca);
  boost::serialization::split_member(ar, *this, version);
}

ECOSTRESS_IMPLEMENT(SimulatedRadiance);

void SimulatedRadiance::init()
{
}

void SimulatedRadiance::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "SimulatedRadiance:\n";
  Os << "  GroundCoordinateArray:\n";
  opad << *gca_;
  opad.strict_sync();
}
