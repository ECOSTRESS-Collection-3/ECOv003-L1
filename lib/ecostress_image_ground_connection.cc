#include "ecostress_image_ground_connection.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
#include <boost/make_shared.hpp>
using namespace Ecostress;

template<class Archive>
void EcostressImageGroundConnection::serialize(Archive & ar,
					       const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(ImageGroundConnection)
    & GEOCAL_NVP(b) & GEOCAL_NVP(res) & GEOCAL_NVP(max_h)
    & GEOCAL_NVP(orb)
    & GEOCAL_NVP(tt)
    & GEOCAL_NVP(cam)
    & GEOCAL_NVP(sm);
}

ECOSTRESS_IMPLEMENT(EcostressImageGroundConnection);

//-------------------------------------------------------------------------
/// Constructor.
//-------------------------------------------------------------------------

EcostressImageGroundConnection::EcostressImageGroundConnection
(const boost::shared_ptr<GeoCal::Orbit>& Orb,
 const boost::shared_ptr<GeoCal::TimeTable>& Tt,
 const boost::shared_ptr<GeoCal::Camera>& Cam,
 const boost::shared_ptr<EcostressScanMirror>& Scan_mirror,
 const boost::shared_ptr<GeoCal::Dem>& D,
 const boost::shared_ptr<GeoCal::RasterImage>& Img,
 const std::string& Title,
 double Res,
 int Band,
 double Max_height)
  : ImageGroundConnection(D, Img,
			  boost::shared_ptr<GeoCal::RasterImageMultiBand>(),
			  Title),
    b(Band),
    res(Res),
    max_h(Max_height),
    orb(Orb),
    tt(Tt),
    cam(Cam),
    sm(Scan_mirror)
{
}

// See base class for description
boost::shared_ptr<GeoCal::GroundCoordinate> 
EcostressImageGroundConnection::ground_coordinate_dem
(const GeoCal::ImageCoordinate& Ic,
 const GeoCal::Dem& D) const
{
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc;
  tt->time(Ic, t, fc);
  return orbit_data(t, Ic.sample)->surface_intersect(*cam, fc, D, res, b, max_h);
}

// See base class for description
boost::shared_ptr<GeoCal::GroundCoordinate> 
EcostressImageGroundConnection::ground_coordinate_approx_height
(const GeoCal::ImageCoordinate& Ic,
 double H) const
{
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc;
  tt->time(Ic, t, fc);
  return orbit_data(t, Ic.sample)->reference_surface_intersect_approximate(*cam, fc, b, H);
}

//-----------------------------------------------------------------------
/// Return orbit data for the given time, which has the scan mirror angle
/// applied to it.
//-----------------------------------------------------------------------

boost::shared_ptr<GeoCal::QuaternionOrbitData>
EcostressImageGroundConnection::orbit_data
(const GeoCal::Time& T, double Ic_sample) const
{
  boost::shared_ptr<GeoCal::QuaternionOrbitData> od =
   boost::dynamic_pointer_cast<GeoCal::QuaternionOrbitData>(orb->orbit_data(T));
  if(!od)
    throw GeoCal::Exception("EcostressImageGroundConnection only works with orbits that return a QuaternionOrbitData");
  boost::shared_ptr<GeoCal::QuaternionOrbitData> res =
    boost::make_shared<GeoCal::QuaternionOrbitData>(*od);
  res->sc_to_ci(od->sc_to_ci() * sm->rotation_quaterion(Ic_sample));
  return res;
}

boost::shared_ptr<GeoCal::QuaternionOrbitData>
EcostressImageGroundConnection::orbit_data
(const GeoCal::TimeWithDerivative& T,
 const GeoCal::AutoDerivative<double>& Ic_sample) const
{
  boost::shared_ptr<GeoCal::QuaternionOrbitData> od =
   boost::dynamic_pointer_cast<GeoCal::QuaternionOrbitData>(orb->orbit_data(T));
  if(!od)
    throw GeoCal::Exception("EcostressImageGroundConnection only works with orbits that return a QuaternionOrbitData");
  boost::shared_ptr<GeoCal::QuaternionOrbitData> res =
    boost::make_shared<GeoCal::QuaternionOrbitData>(*od);
  res->sc_to_ci_with_derivative(od->sc_to_ci_with_derivative() * sm->rotation_quaterion(Ic_sample));
  return res;
}

// See base class for description
void EcostressImageGroundConnection::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "EcostressImageGroundConnection\n"
     << "  Title:      " << title() << "\n"
     << "  Resolution: " << resolution() << "\n"
     << "  Band:       " << band() << "\n"
     << "  Max height: " << max_height() << "\n"
     << "  Orbit: \n";
    opad << *orb;
    opad.strict_sync();
    Os << "  Time table: \n";
    opad << *tt;
    opad.strict_sync();
    Os << "  Camera: \n";
    opad << *cam;
    opad.strict_sync();
    Os << "  Scan mirror: \n";
    opad << *sm;
    opad.strict_sync();
    Os << "  Dem: \n";
    opad << dem();
    opad.strict_sync();
    Os << "  Image: \n";
    if(image())
      opad << *image();
    else
      opad << "Missing image\n";
    opad.strict_sync();
}

GeoCal::ImageCoordinate EcostressImageGroundConnection::image_coordinate
(const GeoCal::GroundCoordinate& Gp) const
{
  boost::shared_ptr<EcostressTimeTable> ett =
    boost::dynamic_pointer_cast<EcostressTimeTable>(tt);
  if(!ett)
    throw GeoCal::Exception("image_coordinate currently only works with EcostressTimeTable");
  GeoCal::ImageCoordinate ic;
  double best_line = -1e20;
  for(int i = 0; i < ett->number_scan(); ++i) {
    SampleFunc f(*this, i, Gp);
    if(f.line_in_range()) {
      double ln = f.fc_at_sol().line;
      if(ln > best_line) {
	best_line = ln;
	ic = f.image_coordinate();
      }
    }
  }
  if(best_line < -1e19)
    throw GeoCal::ImageGroundConnectionFailed();
  return ic;
}

//-----------------------------------------------------------------------
/// Image coordinate for a particular scan index (useful for example
/// to do band to band registration).
///
/// This indicates success by setting Success to true if we were able
/// to fill in Ic, false otherwise
///
/// Because it is convenient, you can pass in a band to use if
/// desired, which can be different than the current value of
/// band(). The default value of -1 means to use the value of band()
/// and not change this.
//-----------------------------------------------------------------------

void EcostressImageGroundConnection::image_coordinate_scan_index
(const GeoCal::GroundCoordinate& Gc,
 int Scan_index, GeoCal::ImageCoordinate& Ic, bool& Success, int Band) const
{
  int start_band = band();
  if(Band != -1)
    const_cast<EcostressImageGroundConnection*>(this)->band(Band);
  try {
    SampleFunc f(*this, Scan_index, Gc);
    Success = false;
    if(f.line_in_range()) {
      Ic = f.image_coordinate();
      Success = true;
    }
    if(Band != -1)
      const_cast<EcostressImageGroundConnection*>(this)->band(start_band);
  } catch(...) {
    if(Band != -1)
      const_cast<EcostressImageGroundConnection*>(this)->band(start_band);
    throw;
  }
}

// See base class for description
blitz::Array<double, 2> 
EcostressImageGroundConnection::image_coordinate_jac_parm
(const GeoCal::GroundCoordinate& Gc) const
{
 boost::shared_ptr<EcostressTimeTable> ett =
    boost::dynamic_pointer_cast<EcostressTimeTable>(tt);
  if(!ett)
    throw GeoCal::Exception("image_coordinate currently only works with EcostressTimeTable");
  GeoCal::ImageCoordinateWithDerivative ic;
  double best_line = -1e20;
  for(int i = 0; i < ett->number_scan(); ++i) {
    SampleFuncWithDerivative f(*this, i, Gc);
    if(f.line_in_range()) {
      double ln = f.fc_at_sol().line.value();
      if(ln > best_line) {
	best_line = ln;
	ic = f.image_coordinate();
      }
    }
  }
  if(best_line < -1e19)
    throw GeoCal::ImageGroundConnectionFailed();
  blitz::Array<double, 2> res(2, std::max(ic.line.number_variable(), 
				   ic.sample.number_variable()));
  if(!ic.line.is_constant())
    res(0, blitz::Range::all()) = ic.line.gradient();
  else
    res(0, blitz::Range::all()) = 0;
  if(!ic.sample.is_constant())
    res(1, blitz::Range::all()) = ic.sample.gradient();
  else
    res(1, blitz::Range::all()) = 0;
  return res; 
}
