// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_igc_collection.h"
%}
%geocal_base_import(igc_array)
%import "geocal_time.i"
%import "ecostress_image_ground_connection.i"
%import "ecostress_image_ground_connection_subset.i"
%ecostress_shared_ptr(Ecostress::EcostressIgcCollection);
namespace Ecostress {
class EcostressIgcCollection : public GeoCal::IgcArray {
public:
  EcostressIgcCollection();
  void nearest_attitude_time_point(const boost::shared_ptr<GeoCal::Time>& T,
				   boost::shared_ptr<GeoCal::Time>& OUTPUT,
				   boost::shared_ptr<GeoCal::Time>& OUTPUT) const;
  %python_attribute_with_set(orbit, boost::shared_ptr<GeoCal::Orbit>);
  %python_attribute_with_set(camera, boost::shared_ptr<GeoCal::Camera>);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressIgcCollection")

