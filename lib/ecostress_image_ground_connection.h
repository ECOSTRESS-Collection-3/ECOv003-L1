#ifndef ECOSTRESS_IMAGE_GROUND_CONNECTION_H
#define ECOSTRESS_IMAGE_GROUND_CONNECTION_H
#include "geocal/image_ground_connection.h"
#include "geocal/orbit.h"
#include "geocal/time_table.h"
#include "ecostress_scan_mirror.h"
#include "ecostress_time_table.h"
#include "geocal_gsl_root.h"

namespace Ecostress {
/****************************************************************//**
  This is a ImageGroundConnection for ecostress.

  Note that there is a good deal of overlap between one scan and the
  next. This means the image_coordinate is often multivalued, more
  than one ImageCoordinate goes to the same GroundCoordinate.

  As a matter of convention, we return the smallest line number that
  matches the given GroundCoordinate. This is arbitrary, but gives a
  clear rule.
*******************************************************************/

class EcostressImageGroundConnection :
    public virtual GeoCal::ImageGroundConnection {
public:
  // The y index with the minimum distortion according to the
  // distortion spread sheet is y index of 4. This corresponds to
  // band 1 (0 based, 2 for 1 based).
  // Bands are:
  //  0 - 1.62 micron (SWIR)
  //  1 - 8.28
  //  2 - 8.63
  //  3 - 9.07
  //  4 - 10.52
  //  5 - 12.05
  enum {REF_BAND = 1 };
  EcostressImageGroundConnection
  (const boost::shared_ptr<GeoCal::Orbit>& Orb,
   const boost::shared_ptr<GeoCal::TimeTable>& Tt,
   const boost::shared_ptr<GeoCal::Camera>& Cam,
   const boost::shared_ptr<EcostressScanMirror>& Scan_mirror,
   const boost::shared_ptr<GeoCal::Dem>& D,
   const boost::shared_ptr<GeoCal::RasterImage>& Img,
   const std::string& Title = "",
   double Resolution=30, int Band= REF_BAND, double Max_height=9000);
  virtual ~EcostressImageGroundConnection() {}
  virtual blitz::Array<double, 7> 
  cf_look_vector_arr(int ln_start, int smp_start, int nline, int nsamp,
		     int nsubpixel_line = 1, 
		     int nsubpixel_sample = 1,
		     int nintegration_step = 1) const
  { throw GeoCal::Exception("Need to implement this.\n"); }
  virtual void
  cf_look_vector(const GeoCal::ImageCoordinate& Ic,
		 GeoCal::CartesianFixedLookVector& Lv,
		 boost::shared_ptr<GeoCal::CartesianFixed>& P) const
  { throw GeoCal::Exception("Need to implement this.\n"); }
  virtual blitz::Array<double, 1> 
  collinearity_residual(const GeoCal::GroundCoordinate& Gc,
			const GeoCal::ImageCoordinate& Ic_actual) const;
  virtual blitz::Array<double, 2> 
  collinearity_residual_jacobian(const GeoCal::GroundCoordinate& Gc,
		        const GeoCal::ImageCoordinate& Ic_actual) const;
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_dem(const GeoCal::ImageCoordinate& Ic,
			const GeoCal::Dem& D) const;
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_approx_height(const GeoCal::ImageCoordinate& Ic, 
				  double H) const;
  virtual GeoCal::ImageCoordinate image_coordinate
  (const GeoCal::GroundCoordinate& Gc) const;
  virtual blitz::Array<double, 2> 
  image_coordinate_jac_parm(const GeoCal::GroundCoordinate& Gc) const;
  virtual void print(std::ostream& Os) const;
  bool crosses_dateline() const;
  virtual int number_line() const { return tt->max_line() + 1; }
  virtual int number_sample() const { return sm->number_sample(); }
  virtual int number_band() const { return cam->number_band(); }
  int number_line_scan() const
  {
    boost::shared_ptr<EcostressTimeTable> ett
      (boost::dynamic_pointer_cast<EcostressTimeTable>(time_table()));
    // We can worry about generalizing this if it ever becomes an
    // issue, but for now we assume the time table is an EcostressTimeTable.
    if(!ett)
      throw GeoCal::Exception("image_coordinate currently only works with EcostressTimeTable");
    return ett->number_line_scan();
  }
  void image_coordinate_scan_index(const GeoCal::GroundCoordinate& Gc,
				   int Scan_index,
				   GeoCal::ImageCoordinate& Ic,
				   bool& Success,
				   int Band = -1) const;
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::Time& T, double Ic_line, double Ic_sample) const;
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::TimeWithDerivative& T, double Ic_line,
   const GeoCal::AutoDerivative<double>& Ic_sample) const;
  virtual bool has_time() const { return true; }
  virtual GeoCal::Time pixel_time(const GeoCal::ImageCoordinate& Ic) const
  {
    GeoCal::Time t;
    GeoCal::FrameCoordinate fc;
    tt->time(Ic,t,fc);
    return t;
  }
    
    
//-----------------------------------------------------------------------
/// Camera band we are using.
//-----------------------------------------------------------------------

  int band() const { return b; }

//-----------------------------------------------------------------------
/// Set camera band we are using.
//-----------------------------------------------------------------------

  void band(int B) { range_check(B, 0, number_band()); b = B; }

//-------------------------------------------------------------------------
/// Orbit we are using.
//-------------------------------------------------------------------------
  
  const boost::shared_ptr<GeoCal::Orbit>& orbit() const { return orb; }
  
//-------------------------------------------------------------------------
/// Set Orbit we are using.
//-------------------------------------------------------------------------
  
  void orbit(const boost::shared_ptr<GeoCal::Orbit>& Orb) { orb = Orb; }

//-------------------------------------------------------------------------
/// TimeTable we are using.
//-------------------------------------------------------------------------
  
  const boost::shared_ptr<GeoCal::TimeTable>& time_table() const { return tt; }

//-------------------------------------------------------------------------
/// Set TimeTable we are using.
//-------------------------------------------------------------------------
  
  void time_table(const boost::shared_ptr<GeoCal::TimeTable>& Tt)
  { tt = Tt; }

//-------------------------------------------------------------------------
/// Camera we are using.
//-------------------------------------------------------------------------
  
  const boost::shared_ptr<GeoCal::Camera>& camera() const { return cam; }

//-------------------------------------------------------------------------
/// Set Camera we are using.
//-------------------------------------------------------------------------
  
  void camera(const boost::shared_ptr<GeoCal::Camera>& Cam)
  { cam = Cam; }

//-------------------------------------------------------------------------
/// EcostressScanMirror we are using.
//-------------------------------------------------------------------------

  const boost::shared_ptr<EcostressScanMirror>& scan_mirror() const
  {return sm; }

//-------------------------------------------------------------------------
/// Set EcostressScanMirror we are using.
//-------------------------------------------------------------------------
  
  void scan_mirror(const boost::shared_ptr<EcostressScanMirror>& Sm)
  { sm = Sm; }

//-----------------------------------------------------------------------
/// Resolution in meters that we examine Dem at. This affects how
/// long ground_coordinate takes to figure out. It should be about the
/// resolution of the Dem
//-----------------------------------------------------------------------

  double resolution() const { return res; }

//-----------------------------------------------------------------------
/// Set resolution in meters that we examine Dem at. This affects how
/// long ground_coordinate takes to figure out. It should be about the
/// resolution of the Dem
//-----------------------------------------------------------------------

  void resolution(double R) { res = R; }

//-----------------------------------------------------------------------
/// Maximum height that we expect to see in the Dem.
//-----------------------------------------------------------------------

  double max_height() const {return max_h;}

//-----------------------------------------------------------------------
/// Set Maximum height that we expect to see in the Dem.
//-----------------------------------------------------------------------

  void max_height(double Max_h) { max_h = Max_h;}

private:
  int b;
  double res, max_h;
  boost::shared_ptr<GeoCal::Orbit> orb;
  boost::shared_ptr<GeoCal::TimeTable> tt;
  boost::shared_ptr<GeoCal::Camera> cam;
  boost::shared_ptr<EcostressScanMirror> sm;
  EcostressImageGroundConnection() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);

  // Function used by IPI for a single scan index, used in a couple of
  // places so we stick it here.
  class SampleFunc: public GeoCal::DFunctor {
  public:
    SampleFunc(const EcostressImageGroundConnection& Igc, int Scan_index,
	       const GeoCal::GroundCoordinate& Gp);
    virtual ~SampleFunc() {}
    GeoCal::FrameCoordinate fc_at_sol() const;
    bool line_in_range() const;
    GeoCal::ImageCoordinate image_coordinate() const;
    virtual double operator()(const double& Toffset) const;
  private:
    const EcostressImageGroundConnection& igc;
    bool can_solve;
    GeoCal::Time epoch, tsol;
    int scan_index;
    const GeoCal::GroundCoordinate& gp;
    boost::shared_ptr<EcostressTimeTable> tt;
  };

  class SampleFuncWithDerivative: public GeoCal::DFunctorWithDerivative {
  public:
    SampleFuncWithDerivative(const EcostressImageGroundConnection& Igc,
			     int Scan_index,
			     const GeoCal::GroundCoordinate& Gp);
    virtual ~SampleFuncWithDerivative() {}
    GeoCal::FrameCoordinateWithDerivative fc_at_sol() const;
    bool line_in_range() const;
    GeoCal::ImageCoordinateWithDerivative image_coordinate() const;
    virtual double operator()(const double& Toffset) const;
    virtual double df(double Toffset) const;
    virtual GeoCal::AutoDerivative<double> f_with_derivative(double Toffset)
      const;
  private:
    const EcostressImageGroundConnection& igc;
    bool can_solve;
    GeoCal::Time epoch;
    GeoCal::TimeWithDerivative tsol;
    int scan_index;
    const GeoCal::GroundCoordinate& gp;
    boost::shared_ptr<EcostressTimeTable> tt;
  };
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressImageGroundConnection);
#endif
