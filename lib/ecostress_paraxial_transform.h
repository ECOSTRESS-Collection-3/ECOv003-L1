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
    : paraxial_to_real_(2, 10),
      real_to_paraxial_(2, 10)
  {}
  virtual ~EcostressParaxialTransform() {}
  virtual void print(std::ostream& Os) const
  { Os << "EcostressParaxialTransform"; }

//-----------------------------------------------------------------------
/// Polynomial from paraxial to real
//-----------------------------------------------------------------------
  const blitz::Array<double, 2>& paraxial_to_real() const
  { return paraxial_to_real_; }
  blitz::Array<double, 2>& paraxial_to_real()
  { return paraxial_to_real_; }

//-----------------------------------------------------------------------
/// Polynomial from real to paraxial
//-----------------------------------------------------------------------
  const blitz::Array<double, 2>& real_to_paraxial() const
  { return real_to_paraxial_; }
  blitz::Array<double, 2>& real_to_paraxial() 
  { return real_to_paraxial_; }
private:
  blitz::Array<double, 2>  paraxial_to_real_, real_to_paraxial_;
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressParaxialTransform);
#endif

  

