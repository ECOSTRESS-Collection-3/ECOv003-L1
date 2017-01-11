#include "ecostress_image_ground_connection.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
using namespace Ecostress;

template<class Archive>
void EcostressImageGroundConnection::serialize(Archive & ar,
					       const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(ImageGroundConnection)
    & GEOCAL_NVP(b)
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
 int Band)
  : ImageGroundConnection(D, Img,
			  boost::shared_ptr<GeoCal::RasterImageMultiBand>(),
			  Title),
    b(Band),
    orb(Orb),
    tt(Tt),
    cam(Cam),
    sm(Scan_mirror)
{
}

// See base class for description
void EcostressImageGroundConnection::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "EcostressImageGroundConnection\n"
     << "  Title:      " << title() << "\n"
     << "  Band:       " << band() << "\n"
     << "  Orbit: \n";
    opad << *orb;
    opad.strict_sync();
    opad.strict_sync();
    Os << "  Time table: \n";
    opad << *tt;
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
