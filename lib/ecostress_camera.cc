#include "ecostress_camera.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
#include <boost/make_shared.hpp>
using namespace Ecostress;

template<class Archive>
void EcostressCamera::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(QuaternionCamera)
    & GEOCAL_NVP_(paraxial_transform);
}

ECOSTRESS_IMPLEMENT(EcostressCamera);

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
  paraxial_transform_ = boost::make_shared<EcostressParaxialTransform>();
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
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "EcostressCamera\n";
  opad << *paraxial_transform_ << "\n";
  opad.strict_sync();
}

// See base class for description

void EcostressCamera::dcs_to_focal_plane(int Band,
				    const boost::math::quaternion<double>& Dcs,
				    double& Xfp, double& Yfp) const
{
//---------------------------------------------------------
// Go to paraxial focal plane. Units are millimeters.
//---------------------------------------------------------

  double yf = (focal_length() / Dcs.R_component_4()) * (-Dcs.R_component_2());
  double xf = (focal_length() / Dcs.R_component_4()) * Dcs.R_component_3();

//-------------------------------------------------------------------------
// Transform paraxial focal plane coordinate to real focal plane coordinate.
// Units are millimeters.
//-------------------------------------------------------------------------
  
  paraxial_transform_->paraxial_to_real(xf, yf, Xfp, Yfp);
}

void EcostressCamera::dcs_to_focal_plane
(int Band,
 const boost::math::quaternion<GeoCal::AutoDerivative<double> >& Dcs,
 GeoCal::AutoDerivative<double>& Xfp, GeoCal::AutoDerivative<double>& Yfp) const
{
//---------------------------------------------------------
// Go to paraxial focal plane. Units are millimeters.
//---------------------------------------------------------

  GeoCal::AutoDerivative<double> yf = 
    (focal_length() / Dcs.R_component_4()) * (-Dcs.R_component_2());
  GeoCal::AutoDerivative<double> xf = 
    (focal_length() / Dcs.R_component_4()) * Dcs.R_component_3();

//-------------------------------------------------------------------------
// Transform paraxial focal plane coordinate to real focal plane coordinate.
// Units are millimeters.
//-------------------------------------------------------------------------
  
  paraxial_transform_->paraxial_to_real(xf, yf, Xfp, Yfp);
}

// See base class for description
boost::math::quaternion<double> 
EcostressCamera::focal_plane_to_dcs(int Band, double Xfp, double Yfp) const
{
//-------------------------------------------------------------------------
/// Convert to paraxial coordinates.
//-------------------------------------------------------------------------

  double xf, yf;
  paraxial_transform_->real_to_paraxial(Xfp, Yfp, xf, yf);

//-------------------------------------------------------------------------
/// Then to detector coordinates look vector.
//-------------------------------------------------------------------------

  return boost::math::quaternion<double>(0, -yf, xf, focal_length());
}

boost::math::quaternion<GeoCal::AutoDerivative<double> >
EcostressCamera::focal_plane_to_dcs
(int Band, const GeoCal::AutoDerivative<double>& Xfp, 
 const GeoCal::AutoDerivative<double>& Yfp) const
{
//-------------------------------------------------------------------------
/// Convert to paraxial coordinates.
//-------------------------------------------------------------------------

  GeoCal::AutoDerivative<double> xf, yf;
  paraxial_transform_->real_to_paraxial(Xfp, Yfp, xf, yf);

//-------------------------------------------------------------------------
/// Then to detector coordinates look vector.
//-------------------------------------------------------------------------

  return boost::math::quaternion<GeoCal::AutoDerivative<double> >(0, -yf, xf, focal_length());
}


