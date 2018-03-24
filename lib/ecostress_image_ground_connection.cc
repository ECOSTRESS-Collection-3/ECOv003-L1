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
/// Constructor
//-------------------------------------------------------------------------

EcostressImageGroundConnection::SampleFunc::SampleFunc
(const EcostressImageGroundConnection& Igc, int Scan_index,
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

//-------------------------------------------------------------------------
/// Constructor
//-------------------------------------------------------------------------

EcostressImageGroundConnection::SampleFuncWithDerivative::SampleFuncWithDerivative
(const EcostressImageGroundConnection& Igc, int Scan_index,
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
    tsol = GeoCal::TimeWithDerivative(epoch) +
      gsl_root_with_derivative(*this, tmin - epoch, tmax - epoch);
    can_solve = true;
  } catch(const GeoCal::ConvergenceFailure& E) {
    // Ok if we fail to get a solution, we just leave can_solve false
  }
}

//-------------------------------------------------------------------------
/// FrameCoordinates at the solution
//-------------------------------------------------------------------------

GeoCal::FrameCoordinate
EcostressImageGroundConnection::SampleFunc::fc_at_sol() const
{
  double sample =
    tt->image_coordinate(tsol, GeoCal::FrameCoordinate(0,0)).sample;
  return igc.orbit_data(tsol, sample)->frame_coordinate(gp, *igc.camera(), igc.band());
}

//-------------------------------------------------------------------------
/// FrameCoordinates at the solution
//-------------------------------------------------------------------------

GeoCal::FrameCoordinateWithDerivative
EcostressImageGroundConnection::SampleFuncWithDerivative::fc_at_sol() const
{
  GeoCal::AutoDerivative<double> sample =
    tt->image_coordinate_with_derivative(tsol, GeoCal::FrameCoordinateWithDerivative(0,0)).sample;
  return igc.orbit_data(tsol, sample)->frame_coordinate_with_derivative(gp, *igc.camera(), igc.band());
}

//-------------------------------------------------------------------------
/// Return true if line coordinate is in the range of the camera.
//-------------------------------------------------------------------------

bool EcostressImageGroundConnection::SampleFunc::line_in_range() const
{
  if(!can_solve)
    return false;
  double ln = fc_at_sol().line;
  return ln >= 0 && ln <= igc.camera()->number_line(igc.band());
}

//-------------------------------------------------------------------------
/// Return true if line coordinate is in the range of the camera.
//-------------------------------------------------------------------------

bool EcostressImageGroundConnection::SampleFuncWithDerivative::line_in_range() const
{
  if(!can_solve)
    return false;
  double ln = fc_at_sol().line.value();
  return ln >= 0 && ln <= igc.camera()->number_line(igc.band());
}

//-------------------------------------------------------------------------
/// ImageCoordinates at the solution
//-------------------------------------------------------------------------

GeoCal::ImageCoordinate
EcostressImageGroundConnection::SampleFunc::image_coordinate() const
{
  if(!can_solve)
    throw GeoCal::Exception("Can't solve");
  return tt->image_coordinate(tsol, fc_at_sol());
}

//-------------------------------------------------------------------------
/// ImageCoordinates at the solution
//-------------------------------------------------------------------------

GeoCal::ImageCoordinateWithDerivative
EcostressImageGroundConnection::SampleFuncWithDerivative::image_coordinate() const
{
  if(!can_solve)
    throw GeoCal::Exception("Can't solve");
  return tt->image_coordinate_with_derivative(tsol, fc_at_sol());
}

//-------------------------------------------------------------------------
/// Function used by solver
//-------------------------------------------------------------------------

double EcostressImageGroundConnection::SampleFunc::operator()
  (const double& Toffset) const
{
  double sample =
    tt->image_coordinate(epoch + Toffset,
			 GeoCal::FrameCoordinate(0,0)).sample;
  return igc.orbit_data(epoch + Toffset, sample)->frame_coordinate(gp, *igc.camera(), igc.band()).sample;
}

//-------------------------------------------------------------------------
/// Function used by solver
//-------------------------------------------------------------------------

double EcostressImageGroundConnection::SampleFuncWithDerivative::operator()
  (const double& Toffset) const
{
  double sample =
    tt->image_coordinate(epoch + Toffset,
			 GeoCal::FrameCoordinate(0,0)).sample;
  return igc.orbit_data(epoch + Toffset, sample)->frame_coordinate(gp, *igc.camera(), igc.band()).sample;
}

//-------------------------------------------------------------------------
/// Derivative with respect to Toffset
//-------------------------------------------------------------------------

double EcostressImageGroundConnection::SampleFuncWithDerivative::df
(double Toffset) const
{
  // Do this numerically for now, we can revisit this if needed
  const double delta = 1e-4;
  return ((*this)(Toffset + delta) - (*this)(Toffset)) / delta;
}

//-------------------------------------------------------------------------
/// Derivative with respect to parameters
//-------------------------------------------------------------------------
GeoCal::AutoDerivative<double>
EcostressImageGroundConnection::SampleFuncWithDerivative::f_with_derivative
(double Toffset) const
{
  GeoCal::AutoDerivative<double> sample =
    tt->image_coordinate_with_derivative
    (GeoCal::TimeWithDerivative(epoch) + Toffset,
     GeoCal::FrameCoordinateWithDerivative(0,0)).sample;
  return igc.orbit_data(GeoCal::TimeWithDerivative(epoch) + Toffset, sample)->frame_coordinate_with_derivative(gp, *igc.camera(), igc.band()).sample;
}

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
  // Not sure what the problem is, but the jacobian we calculate with
  // AutoDerivative doesn't agree at all with the finite difference
  // jacobian for the sample coordinate (line agrees pretty
  // well). Spent a bit of time trying to track this down, but
  // couldn't find the problem. We don't actually use this for the
  // sba, since we override the collinearity_residual function. So for
  // now, just throw an exception if this is called. If this ever ends
  // up mattering, we can work through this and try to figure out
  // whatever the problem is here.
  // There is a stubbed out unit test in ecostress_igc_collection_test.cc
  // (so *not* ecostress_image_ground_connection_test.cc because
  // easier set up with a full collection) that illustrates the problem.

  throw GeoCal::Exception("Not implemented");

  // Leave the rest of the code in place, but we don't actually execute
  // any of it.
  
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

blitz::Array<double, 1> 
EcostressImageGroundConnection::collinearity_residual
(const GeoCal::GroundCoordinate& Gc,
 const GeoCal::ImageCoordinate& Ic_actual) const
{
  // Instead of the difference in ImageCoordinates returned by the
  // Ipi, use the difference in the FrameCoordinate for the time
  // associated with Ic_actual. This is faster to calculate, and the
  // Jacobian is much better behaved.
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc_actual;
  tt->time(Ic_actual, t, fc_actual);
  GeoCal::FrameCoordinate fc_predict = orbit_data(t, Ic_actual.sample)->
    frame_coordinate(Gc, *cam, b);
  blitz::Array<double, 1> res(2);
  res(0) = fc_predict.line - fc_actual.line;
  res(1) = fc_predict.sample - fc_actual.sample;
  return res;
}

blitz::Array<double, 2> 
EcostressImageGroundConnection::collinearity_residual_jacobian
(const GeoCal::GroundCoordinate& Gc,
 const GeoCal::ImageCoordinate& Ic_actual) const
{
  GeoCal::TimeWithDerivative t;
  GeoCal::FrameCoordinateWithDerivative fc_actual;
  GeoCal::ImageCoordinateWithDerivative ica(Ic_actual.line, Ic_actual.sample);
  tt->time_with_derivative(ica, t, fc_actual);
  GeoCal::FrameCoordinateWithDerivative fc_predict = orbit_data(t, ica.sample)->
    frame_coordinate_with_derivative(Gc, *cam, b);
  blitz::Array<double, 2> res(2, fc_predict.line.number_variable() + 3);
  res(0, blitz::Range(0, res.cols() - 4)) = 
    (fc_predict.line - fc_actual.line).gradient();
  res(1, blitz::Range(0, res.cols() - 4)) = 
    (fc_predict.sample - fc_actual.sample).gradient();

  // Part of jacobian for cf coordinates.
  boost::shared_ptr<GeoCal::OrbitData> od = orbit_data(t.value(), Ic_actual.sample);
  boost::shared_ptr<GeoCal::CartesianFixed> p1 = od->position_cf();
  boost::shared_ptr<GeoCal::CartesianFixed> p2 = Gc.convert_to_cf();
  GeoCal::CartesianFixedLookVectorWithDerivative lv;
  for(int i = 0; i < 3; ++i) {
    GeoCal::AutoDerivative<double> p(p2->position[i], i, 3);
    lv.look_vector[i] = p - p1->position[i];
  }
  GeoCal::ScLookVectorWithDerivative sl = od->sc_look_vector(lv);
  boost::shared_ptr<GeoCal::Camera> c = cam;
  GeoCal::ArrayAd<double, 1> poriginal = c->parameter_with_derivative();
  c->parameter_with_derivative(c->parameter());
  GeoCal::FrameCoordinateWithDerivative fc_gc =
    c->frame_coordinate_with_derivative(sl, b);
  c->parameter_with_derivative(poriginal);
  res(0, blitz::Range(res.cols() - 3, blitz::toEnd)) = fc_gc.line.gradient();
  res(1, blitz::Range(res.cols() - 3, blitz::toEnd)) = fc_gc.sample.gradient();
  return res;
}

