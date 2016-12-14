#include "ecostress_camera.h"
#include "geocal/geocal_serialize_support.h"

using namespace Ecostress;

template<class Archive>
void EcostressCamera::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(QuaternionCamera);
}

BOOST_CLASS_EXPORT_IMPLEMENT(Ecostress::EcostressCamera);

//-----------------------------------------------------------------------
/// Constructor. Right now we have everything hardcoded, we'll change
/// this to use a configuration file in the future.
//-----------------------------------------------------------------------

EcostressCamera::EcostressCamera()
  : QuaternionCamera(boost::math::quaternion<double>(1,0,0,0), 256, 1,
		     40e-3, 40e-3, 425, GeoCal::FrameCoordinate(128,0.5),
		     QuaternionCamera::LINE_IS_X,
		     QuaternionCamera::INCREASE_IS_NEGATIVE,
		     QuaternionCamera::INCREASE_IS_NEGATIVE)
{
  // This information comes from https://bravo-lib.jpl.nasa.gov/docushare/dsweb/Get/Document-1882647/FPA%20distortion20140522.xlsx
  nband_ = 6;
  principal_point_.resize(number_band());
  parameter_mask_.resize(6 + 2 * number_band());
  parameter_mask_ = true;
  // Using 1 based bands, we have:
  // y index on CCD  ecostress band
  // 2               6
  // 3               1
  // 4               5
  // 5               4
  // 6               2
  // 7               3
  //
  // And then (not counting distortion)
  // frame to dcs (ignoring nonlinearity in optics)
  // y = (ccd y index - 4.5) * (32) * -0.04 mm
  // x = (line - 128) * -0.04
  blitz::Array<int, 1> yindex(6);
  yindex = 3, 6, 7, 5, 4, 2;
  for(int i = 0; i < yindex.rows(); ++i)
    principal_point_[i] = GeoCal::FrameCoordinate(128, -(yindex(i) - 4.5) * 32);
  // Not sure about orientation of this
}

/// See base class for description
void EcostressCamera::print(std::ostream& Os) const
{
  Os << "EcostressCamera";
}
