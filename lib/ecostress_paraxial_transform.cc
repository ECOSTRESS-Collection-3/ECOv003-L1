#include "ecostress_paraxial_transform.h"
#include "geocal/geocal_serialize_support.h"

using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressParaxialTransform::serialize(Archive & ar, const unsigned int version)
{
  boost::serialization::void_cast_register<EcostressParaxialTransform,
					   GeoCal::GenericObject>();
  ar & GEOCAL_NVP_(par_to_real)
    & GEOCAL_NVP_(real_to_par);
}

BOOST_CLASS_EXPORT_IMPLEMENT(Ecostress::EcostressParaxialTransform);

//-----------------------------------------------------------------------
/// Convert pariaxial to real coordinates.
//-----------------------------------------------------------------------
  
void EcostressParaxialTransform::paraxial_to_real
(double x, double y, double& Real_x, double& Real_y) const
{
  double x2 = x * x;
  double y2 = y * y;
  double x3 = x * x2;
  double y3 = y * y2;
  // We get the order of these polynomial powers using
  // ecostress_camera_generate.py
  const blitz::Array<double, 2>& p = par_to_real_;
  Real_x = p(0,0) + p(0,1) * x + p(0,2) * y + p(0,3)*x2 +
    p(0,4)*x*y + p(0,5)*y2 + p(0,6)*x3 +p(0,7)*x2*y +
    p(0,8)*x*y2 + p(0,9)*y3;
  Real_y = p(1,0) + p(1,1) * x + p(1,2) * y + p(1,3)*x2 +
    p(1,4)*x*y + p(1,5)*y2 + p(1,6)*x3 +p(1,7)*x2*y +
    p(1,8)*x*y2 + p(1,9)*y3;
}

//-----------------------------------------------------------------------
/// Convert pariaxial to real coordinates.
//-----------------------------------------------------------------------
  
void EcostressParaxialTransform::paraxial_to_real
(const AutoDerivative<double>& x,
 const AutoDerivative<double>& y,
 AutoDerivative<double>& Real_x, 
 AutoDerivative<double>& Real_y) const
{
  AutoDerivative<double> x2 = x * x;
  AutoDerivative<double> y2 = y * y;
  AutoDerivative<double> x3 = x * x2;
  AutoDerivative<double> y3 = y * y2;
  // We get the order of these polynomial powers using
  // ecostress_camera_generate.py
  const blitz::Array<double, 2>& p = par_to_real_;
  Real_x = p(0,0) + p(0,1) * x + p(0,2) * y + p(0,3)*x2 +
    p(0,4)*x*y + p(0,5)*y2 + p(0,6)*x3 +p(0,7)*x2*y +
    p(0,8)*x*y2 + p(0,9)*y3;
  Real_y = p(1,0) + p(1,1) * x + p(1,2) * y + p(1,3)*x2 +
    p(1,4)*x*y + p(1,5)*y2 + p(1,6)*x3 +p(1,7)*x2*y +
    p(1,8)*x*y2 + p(1,9)*y3;
}

//-----------------------------------------------------------------------
/// Convert real to pariaxial coordinates.
//-----------------------------------------------------------------------
  
void EcostressParaxialTransform::real_to_paraxial
(double x, double y, double& Paraxial_x, double& Paraxial_y) const
{
  double x2 = x * x;
  double y2 = y * y;
  double x3 = x * x2;
  double y3 = y * y2;
  // We get the order of these polynomial powers using
  // ecostress_camera_generate.py
  const blitz::Array<double, 2>& p = real_to_par_;
  Paraxial_x = p(0,0) + p(0,1) * x + p(0,2) * y + p(0,3)*x2 +
    p(0,4)*x*y + p(0,5)*y2 + p(0,6)*x3 +p(0,7)*x2*y +
    p(0,8)*x*y2 + p(0,9)*y3;
  Paraxial_y = p(1,0) + p(1,1) * x + p(1,2) * y + p(1,3)*x2 +
    p(1,4)*x*y + p(1,5)*y2 + p(1,6)*x3 +p(1,7)*x2*y +
    p(1,8)*x*y2 + p(1,9)*y3;
}

//-----------------------------------------------------------------------
/// Convert real to pariaxial coordinates.
//-----------------------------------------------------------------------
  
void EcostressParaxialTransform::real_to_paraxial
(const AutoDerivative<double>& x,
 const AutoDerivative<double>& y,
 AutoDerivative<double>& Paraxial_x, 
 AutoDerivative<double>& Paraxial_y) const
{
  AutoDerivative<double> x2 = x * x;
  AutoDerivative<double> y2 = y * y;
  AutoDerivative<double> x3 = x * x2;
  AutoDerivative<double> y3 = y * y2;
  // We get the order of these polynomial powers using
  // ecostress_camera_generate.py
  const blitz::Array<double, 2>& p = real_to_par_;
  Paraxial_x = p(0,0) + p(0,1) * x + p(0,2) * y + p(0,3)*x2 +
    p(0,4)*x*y + p(0,5)*y2 + p(0,6)*x3 +p(0,7)*x2*y +
    p(0,8)*x*y2 + p(0,9)*y3;
  Paraxial_y = p(1,0) + p(1,1) * x + p(1,2) * y + p(1,3)*x2 +
    p(1,4)*x*y + p(1,5)*y2 + p(1,6)*x3 +p(1,7)*x2*y +
    p(1,8)*x*y2 + p(1,9)*y3;
}

