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
  return boost::make_shared<GeoCal::QuaternionOrbitData>
    (od->time(), od->position_ci(), od->velocity_ci(),
     od->sc_to_ci() * sm->rotation_quaterion(Ic_sample));
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
