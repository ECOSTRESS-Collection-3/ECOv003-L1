// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_orbit_offset_correction.h"
%}

%geocal_base_import(orbit)

%ecostress_shared_ptr(Ecostress::EcostressOrbitOffsetCorrection);
namespace Ecostress {
class EcostressOrbitOffsetCorrection : public GeoCal::Orbit {
public:
  EcostressOrbitOffsetCorrection(const boost::shared_ptr<GeoCal::Orbit> Orb_uncorr);
  virtual boost::shared_ptr<GeoCal::OrbitData> orbit_data(GeoCal::Time T) const;
  virtual boost::shared_ptr<GeoCal::OrbitData> orbit_data(const GeoCal::TimeWithDerivative& T) 
    const;
  void add_scene(int Scene_number, GeoCal::Time& Tstart, GeoCal::Time& Tend);
  %python_attribute(orbit_uncorrected, boost::shared_ptr<GeoCal::Orbit>);
  std::vector<int> scene_list() const;
  %pickle_serialization();
};

}

// List of things "import *" will include
%python_export("EcostressOrbitOffsetCorrection", )

