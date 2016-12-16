#ifndef ECOSTRESS_PARAXIAL_TRANSFORM_H
#define ECOSTRESS_PARAXIAL_TRANSFORM_H
#include "geocal/printable.h"
#include "geocal/auto_derivative.h"
#include <blitz/array.h>

namespace Ecostress {
/****************************************************************//**
  This handles the non-linearity of the ECOSTRESS camera optics. This
  goes to and from real frame camera coordinate (i.e. x and y of the
  CCD) and the location we'd get for a pinhole camera with no
  non-linearity (the paraxial approximation).

  Turns out that a 3rd order polynomial does a pretty good job
  capturing the distortion. We have a difference with the calculated
  distortion has a maximum difference of 0.02 pixels.

  Note that this is likely to get replaced with something else when we
  have the real camera model.

  Currently we fill out this data using the script
  ecostress_camera_generate.py in the end_to_end_testing/ directory.
*******************************************************************/
class EcostressParaxialTransform: public GeoCal::Printable<EcostressParaxialTransform> {
public:
//-----------------------------------------------------------------------
/// We populate the transform separately, so just have a default
/// constructor. A 3rd order polynomial has 10 coefficients
/// (calculated in ecostress_camera_generate.py).
//-----------------------------------------------------------------------
  EcostressParaxialTransform()
    : par_to_real_(2, 10),
      real_to_par_(2, 10)
  {}
  virtual ~EcostressParaxialTransform() {}
  virtual void print(std::ostream& Os) const
  { Os << "EcostressParaxialTransform"; }

  void paraxial_to_real(double Paraxial_x,
			double Paraxial_y, double& Real_x, 
			double& Real_y) const;
  void paraxial_to_real(const GeoCal::AutoDerivative<double>& Paraxial_x,
			const GeoCal::AutoDerivative<double>& Paraxial_y,
			GeoCal::AutoDerivative<double>& Real_x, 
			GeoCal::AutoDerivative<double>& Real_y) const;
  void real_to_paraxial(double Real_x,
			double Real_y, double& Paraxial_x, 
			double& Paraxial_y) const;
  void real_to_paraxial(const GeoCal::AutoDerivative<double>& Real_x,
			const GeoCal::AutoDerivative<double>& Real_y,
			GeoCal::AutoDerivative<double>& Paraxial_x, 
			GeoCal::AutoDerivative<double>& Paraxial_y) const;

//-----------------------------------------------------------------------
/// Polynomial from paraxial to real
//-----------------------------------------------------------------------

  const blitz::Array<double, 2>& par_to_real() const
  { return par_to_real_; }
  blitz::Array<double, 2>& par_to_real()
  { return par_to_real_; }

//-----------------------------------------------------------------------
/// Polynomial from real to paraxial
//-----------------------------------------------------------------------
  const blitz::Array<double, 2>& real_to_par() const
  { return real_to_par_; }
  blitz::Array<double, 2>& real_to_par() 
  { return real_to_par_; }
private:
  blitz::Array<double, 2>  par_to_real_, real_to_par_;
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressParaxialTransform);
#endif

  

