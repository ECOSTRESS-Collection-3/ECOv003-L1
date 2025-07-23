#include "ecostress_image_ground_connection_subset.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
using namespace Ecostress;

template<class Archive>
void EcostressImageGroundConnectionSubset::serialize(Archive & ar,
					       const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(ImageGroundConnection)
    & GEOCAL_NVP_(igc) & GEOCAL_NVP_(start_sample) & GEOCAL_NVP_(num_sample);
}

ECOSTRESS_IMPLEMENT(EcostressImageGroundConnectionSubset);

// See base class for description
void EcostressImageGroundConnectionSubset::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "EcostressImageGroundConnectionSubset\n"
     << "  Start sample:  " << start_sample_ << "\n"
     << "  Number sample: " << num_sample_ << "\n"
     << "  EcostressImageGroundConnection: \n";
  opad << *igc_;
  opad.strict_sync();
}

