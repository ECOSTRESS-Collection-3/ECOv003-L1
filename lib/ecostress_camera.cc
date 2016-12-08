#include "ecostress_camera.h"
#include "geocal/geocal_serialize_support.h"

using namespace Ecostress;

template<class Archive>
void EcostressCamera::serialize(Archive & ar, const unsigned int version)
{
  //  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(GeoCal::QuaternionCamera);
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(QuaternionCamera);
}

BOOST_CLASS_EXPORT_IMPLEMENT(Ecostress::EcostressCamera);

//-----------------------------------------------------------------------
/// Constructor. Right now we have everything hardcoded, we'll change
/// this to use a configuration file in the future.
//-----------------------------------------------------------------------

EcostressCamera::EcostressCamera()
  : QuaternionCamera(boost::math::quaternion<double>(1,0,0,0), 256, 1,
		     40e-3, 40e-3, 425, GeoCal::FrameCoordinate(128,0.5))
{
}

/// See base class for description
void EcostressCamera::print(std::ostream& Os) const
{
  Os << "EcostressCamera";
}
