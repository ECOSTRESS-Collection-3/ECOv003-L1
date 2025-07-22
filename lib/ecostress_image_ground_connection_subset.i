// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_image_ground_connection_subset.h"
%}
%geocal_base_import(image_ground_connection)
%include "ecostress_image_ground_connection.i"
%ecostress_shared_ptr(Ecostress::EcostressImageGroundConnectionSubset);
namespace Ecostress {
class EcostressImageGroundConnectionSubset : public GeoCal::ImageGroundConnection {
public:
  EcostressImageGroundConnectionSubset
  (const boost::shared_ptr<EcostressImageGroundConnection>& Igc,
   int Start_sample, int Num_sample);
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_dem(const GeoCal::ImageCoordinate& Ic,
			const GeoCal::Dem& D) const;
  virtual GeoCal::ImageCoordinate image_coordinate
  (const GeoCal::GroundCoordinate& Gc) const;
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::Time& T, double Ic_line, double Ic_sample) const;
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::TimeWithDerivative& T, double Ic_line,
   const GeoCal::AutoDerivative<double>& Ic_sample) const;
  %python_attribute(underlying_igc, boost::shared_ptr<EcostressImageGroundConnection>);
  %python_attribute(start_sample, int);
  %python_attribute(sub_camera, boost::shared_ptr<GeoCal::Camera>);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressImageGroundConnectionSubset")

