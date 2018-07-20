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
  // Older version didn't have y_scale and y_offset
  if(version > 0)
    ar & GEOCAL_NVP_(y_scale)
      & GEOCAL_NVP_(y_offset);
  if(version > 1)
    ar & GEOCAL_NVP_(line_order_reversed);
}

ECOSTRESS_IMPLEMENT(EcostressCamera);

//-----------------------------------------------------------------------
/// Constructor. We've hardcoded things we don't expect to change
/// (e.g., the line and sample pitch).
//-----------------------------------------------------------------------

EcostressCamera::EcostressCamera(double Focal_length, double Y_scale,
				 double Y_offset,
				 boost::math::quaternion<double> Frame_to_sc_q,
				 bool Line_order_reversed)
  : QuaternionCamera(Frame_to_sc_q, 256, 1,
		     40e-3, 40e-3, Focal_length,
		     GeoCal::FrameCoordinate(128,0.5),
		     QuaternionCamera::LINE_IS_X,
		     QuaternionCamera::INCREASE_IS_NEGATIVE,
		     QuaternionCamera::INCREASE_IS_NEGATIVE),
    y_scale_(Y_scale), y_offset_(Y_offset), line_order_reversed_(Line_order_reversed)
{
  paraxial_transform_ = boost::make_shared<EcostressParaxialTransform>();
  // This information comes from https://bravo-lib.jpl.nasa.gov/docushare/dsweb/Get/Document-1882647/FPA%20distortion20140522.xlsx
  nband_ = 6;
  principal_point_.resize(number_band());
  parameter_mask_.resize(6 + 2 * number_band());
  parameter_mask_ = true;
  // Using 1 based bands, we have:
  // y index on CCD  ecostress band
  // 2               1
  // 3               6
  // 4               2
  // 5               3
  // 6               5
  // 7               4
  //
  // And then (not counting distortion)
  // frame to dcs (ignoring nonlinearity in optics)
  // y = (ccd y index - 4.5) * (32) * -0.04 mm
  // x = (line - 128) * -0.04
  blitz::Array<int, 1> yindex(6);
  yindex = 2, 4, 5, 7, 6, 3;
  for(int i = 0; i < yindex.rows(); ++i)
    principal_point_[i] = GeoCal::FrameCoordinate(128, (yindex(i) - 4.5) * 32);
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

  double xf = (focal_length() / Dcs.R_component_4()) * Dcs.R_component_2();
  double yf = (focal_length() / Dcs.R_component_4()) * Dcs.R_component_3();
  yf = (yf - y_offset_) / y_scale_;

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

  GeoCal::AutoDerivative<double> xf = 
    (focal_length() / Dcs.R_component_4()) * Dcs.R_component_2();
  GeoCal::AutoDerivative<double> yf = 
    (focal_length() / Dcs.R_component_4()) * Dcs.R_component_3();
  yf = (yf - y_offset_) / y_scale_;
  
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

  yf = y_scale_ * yf + y_offset_;
  
//-------------------------------------------------------------------------
/// Then to detector coordinates look vector.
//-------------------------------------------------------------------------

  return boost::math::quaternion<double>(0, xf, yf, focal_length());
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

  yf = y_scale_ * yf + y_offset_;
  
//-------------------------------------------------------------------------
/// Then to detector coordinates look vector.
//-------------------------------------------------------------------------

  return boost::math::quaternion<GeoCal::AutoDerivative<double> >(0, xf, yf, focal_length());
}


// See base class for description
GeoCal::FrameCoordinate EcostressCamera::focal_plane_to_fc(int Band, double Xfp,
						    double Yfp) const
{
  GeoCal::FrameCoordinate fc =
    GeoCal::QuaternionCamera::focal_plane_to_fc(Band, Xfp, Yfp);
  if(line_order_reversed_)
    fc.line = (nline_ - 1)  - fc.line;
  return fc;
}

// See base class for description

GeoCal::FrameCoordinateWithDerivative EcostressCamera::focal_plane_to_fc
(int Band, const GeoCal::AutoDerivative<double>& Xfp,
 const GeoCal::AutoDerivative<double>& Yfp) const
{
  GeoCal::FrameCoordinateWithDerivative fc =
    GeoCal::QuaternionCamera::focal_plane_to_fc(Band, Xfp, Yfp);
  if(line_order_reversed_)
    fc.line = (nline_ - 1)  - fc.line;
  return fc;
}
  
// See base class for description

void EcostressCamera::fc_to_focal_plane
(const GeoCal::FrameCoordinate& Fc, int Band, double& Xfp, double& Yfp) const
{
  GeoCal::FrameCoordinate t(Fc);
  if(line_order_reversed_)
    t.line = (nline_ - 1)  - t.line;
  GeoCal::QuaternionCamera::fc_to_focal_plane(t, Band, Xfp, Yfp);
}

// See base class for description

void EcostressCamera::fc_to_focal_plane
(const GeoCal::FrameCoordinateWithDerivative& Fc, int Band,
 GeoCal::AutoDerivative<double>& Xfp, GeoCal::AutoDerivative<double>& Yfp) const
{
  GeoCal::FrameCoordinateWithDerivative t(Fc);
  if(line_order_reversed_)
    t.line = (nline_ - 1)  - t.line;
  GeoCal::QuaternionCamera::fc_to_focal_plane(t, Band, Xfp, Yfp);
}
