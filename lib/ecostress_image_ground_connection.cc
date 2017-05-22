#include "ecostress_image_ground_connection.h"
#include "ecostress_time_table.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
#include "geocal_gsl_root.h"
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
  class SampleFunc: public GeoCal::DFunctor {
  public:
    SampleFunc(const EcostressImageGroundConnection& Igc, int Scan_index,
	       const GeoCal::GroundCoordinate& Gp)
      : igc(Igc), can_solve(false), gp(Gp),
	tt(boost::dynamic_pointer_cast<EcostressTimeTable>(Igc.time_table()))
    {
      // We can worry about generalizing this if it ever becomes an
      // issue, but for now we assume the time table is an EcostressTimeTable.
      if(!tt)
	throw GeoCal::Exception("image_coordinate currently only works with EcostressTimeTable");
      epoch = tt->min_time();
      int lstart, lend;
      tt->scan_index_to_line(Scan_index, lstart, lend);
      GeoCal::Time tmin, tmax;
      GeoCal::FrameCoordinate fc;
      tt->time(GeoCal::ImageCoordinate(lstart, 0), tmin, fc);
      tt->time(GeoCal::ImageCoordinate(lstart, Igc.number_sample() - 1), tmax,
	       fc);
      if((*this)(tmin - epoch) * (*this)(tmax - epoch) > 0)
	// Ok if we fail to get a solution, we just leave can_solve false
	return;
      try {
	tsol = epoch + gsl_root(*this, tmin - epoch, tmax - epoch);
	can_solve = true;
      } catch(const GeoCal::ConvergenceFailure& E) {
	// Ok if we fail to get a solution, we just leave can_solve false
      }
    }
    virtual ~SampleFunc() {}
    GeoCal::FrameCoordinate fc_at_sol() const
    {
      double sample =
	tt->image_coordinate(tsol, GeoCal::FrameCoordinate(0,0)).sample;
      return igc.orbit_data(tsol, sample)->frame_coordinate(gp, *igc.camera(), igc.band());
    }
    bool line_in_range() const
    {
      if(!can_solve)
	return false;
      double ln = fc_at_sol().line;
      return ln >= 0 && ln <= igc.camera()->number_line(igc.band());
    }
    GeoCal::ImageCoordinate image_coordinate() const
    {
      if(!can_solve)
	throw GeoCal::Exception("Can't solve");
      return tt->image_coordinate(tsol, fc_at_sol());
    }
    virtual double operator()(const double& Toffset) const
    {
      double sample =
	tt->image_coordinate(epoch + Toffset,
			     GeoCal::FrameCoordinate(0,0)).sample;
      return igc.orbit_data(epoch + Toffset, sample)->frame_coordinate(gp, *igc.camera(), igc.band()).sample;
    }
  private:
    const EcostressImageGroundConnection& igc;
    bool can_solve;
    GeoCal::Time epoch, tsol;
    const GeoCal::GroundCoordinate& gp;
    boost::shared_ptr<EcostressTimeTable> tt;
  };

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
