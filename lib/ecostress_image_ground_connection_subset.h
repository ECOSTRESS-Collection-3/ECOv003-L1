#ifndef ECOSTRESS_IMAGE_GROUND_CONNECTION_SUBSET_H
#define ECOSTRESS_IMAGE_GROUND_CONNECTION_SUBSET_H
#include "ecostress_image_ground_connection.h"
#include <boost/make_shared.hpp>

namespace Ecostress {
/****************************************************************//**
  This is a subset of the EcostressImageGroundConnection, with fewer
  samples. We needed this for a particular investigation (white paper
  for Landsat fill in), but go ahead and leave this in place for
  future use.
*******************************************************************/

class EcostressImageGroundConnectionSubset :
    public virtual GeoCal::ImageGroundConnection {
public:
  EcostressImageGroundConnectionSubset
  (const boost::shared_ptr<EcostressImageGroundConnection>& Igc,
   int Start_sample, int Num_sample)
    : GeoCal::ImageGroundConnection
      (Igc->dem_ptr(),
       boost::make_shared<GeoCal::SubRasterImage>(Igc->image(), 0, Start_sample,
						  Igc->number_line(), Num_sample),
       boost::shared_ptr<GeoCal::RasterImageMultiBand>(),
       Igc->title()),
      igc_(Igc),
      start_sample_(Start_sample),
      num_sample_(Num_sample)
  {
  }
  virtual ~EcostressImageGroundConnectionSubset() {}

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
			const GeoCal::ImageCoordinate& Ic_actual) const
  { return igc_->collinearity_residual(Gc, ic_from_subset(Ic_actual));}
  virtual blitz::Array<double, 2> 
  collinearity_residual_jacobian(const GeoCal::GroundCoordinate& Gc,
		        const GeoCal::ImageCoordinate& Ic_actual) const
  { return igc_->collinearity_residual_jacobian(Gc, ic_from_subset(Ic_actual));}
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_dem(const GeoCal::ImageCoordinate& Ic,
			const GeoCal::Dem& D) const
  { return igc_->ground_coordinate_dem(ic_from_subset(Ic), D);}
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_approx_height(const GeoCal::ImageCoordinate& Ic, 
				  double H) const
  { return igc_->ground_coordinate_approx_height(ic_from_subset(Ic), H);}
  virtual GeoCal::ImageCoordinate image_coordinate
  (const GeoCal::GroundCoordinate& Gc) const
  { return ic_to_subset(igc_->image_coordinate(Gc));}
  virtual blitz::Array<double, 2> 
  image_coordinate_jac_parm(const GeoCal::GroundCoordinate& Gc) const
  { return igc_->image_coordinate_jac_parm(Gc);}
  virtual void print(std::ostream& Os) const;
  virtual int number_line() const { return igc_->number_line(); }
  virtual int number_sample() const { return num_sample_;}
  virtual int number_band() const { return igc_->number_band(); }
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::Time& T, double Ic_line, double Ic_sample) const
  { return igc_->orbit_data(T, Ic_line, Ic_sample + start_sample_); }
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::TimeWithDerivative& T, double Ic_line,
   const GeoCal::AutoDerivative<double>& Ic_sample) const
  { return igc_->orbit_data(T, Ic_line, Ic_sample + start_sample_); }
  virtual bool has_time() const { return true; }
  virtual GeoCal::Time pixel_time(const GeoCal::ImageCoordinate& Ic) const
  { return igc_->pixel_time(ic_from_subset(Ic)); }
    
  const boost::shared_ptr<EcostressImageGroundConnection>& underlying_igc() const
  { return igc_;}
  int start_sample() const { return  start_sample_;}
private:
  GeoCal::ImageCoordinate ic_from_subset(const GeoCal::ImageCoordinate& Ic_subset) const
  {
    GeoCal::ImageCoordinate ic(Ic_subset);
    ic.sample += start_sample_;
    return ic;
  }
  GeoCal::ImageCoordinate ic_to_subset(const GeoCal::ImageCoordinate& Ic_full) const
  {
    GeoCal::ImageCoordinate ic(Ic_full);
    ic.sample -= start_sample_;
    return ic;
  }
  EcostressImageGroundConnectionSubset() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  boost::shared_ptr<EcostressImageGroundConnection> igc_;
  int start_sample_, num_sample_;
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressImageGroundConnectionSubset);
#endif
  

