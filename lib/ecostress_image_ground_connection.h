#ifndef ECOSTRESS_IMAGE_GROUND_CONNECTION_H
#define ECOSTRESS_IMAGE_GROUND_CONNECTION_H
#include "geocal/image_ground_connection.h"
#include "geocal/orbit.h"
#include "geocal/time_table.h"
#include "ecostress_scan_mirror.h"

namespace Ecostress {
/****************************************************************//**
  This is a ImageGroundConnection for ecostress.
*******************************************************************/

class EcostressImageGroundConnection :
    public virtual GeoCal::ImageGroundConnection {
public:
  enum {REF_BAND = 4 }; 	// Not sure about this, we'll need to
				// check on this
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
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_dem(const GeoCal::ImageCoordinate& Ic,
			const GeoCal::Dem& D) const;
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_approx_height(const GeoCal::ImageCoordinate& Ic, 
				  double H) const;
  virtual GeoCal::ImageCoordinate image_coordinate
  (const GeoCal::GroundCoordinate& Gc) const 
  { throw GeoCal::Exception("Need to implement this.\n"); }
  virtual blitz::Array<double, 2> 
  image_coordinate_jac_parm(const GeoCal::GroundCoordinate& Gc) const
  { throw GeoCal::Exception("Need to implement this.\n"); }
  virtual void print(std::ostream& Os) const;

  virtual int number_line() const { return tt->max_line() + 1; }
  virtual int number_sample() const { return sm->number_sample(); }
  virtual int number_band() const { return cam->number_band(); }
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::Time& T, double Ic_sample) const;
    
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
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressImageGroundConnection);
#endif
