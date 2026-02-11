// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "combine_orbit.h"
%}

%geocal_base_import(orbit)

%ecostress_shared_ptr(Ecostress::CombineOrbit);
namespace Ecostress {
class CombineOrbit : public GeoCal::Orbit {
public:
  CombineOrbit();
  void add_orbit(const boost::shared_ptr<GeoCal::Orbit>& orb);
  virtual boost::shared_ptr<GeoCal::OrbitData> orbit_data(GeoCal::Time T) const;
  virtual boost::shared_ptr<GeoCal::OrbitData> orbit_data(const GeoCal::TimeWithDerivative& T) 
    const;
  %python_attribute(orbit_list, const std::vector<boost::shared_ptr<GeoCal::Orbit> >&);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("CombineOrbit")
