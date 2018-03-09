// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_igc_collection.h"
%}
%geocal_base_import(igc_array)
%import "ecostress_image_ground_connection.i"
%ecostress_shared_ptr(Ecostress::EcostressIgcCollection);
namespace Ecostress {
class EcostressIgcCollection : public GeoCal::IgcArray {
public:
  EcostressIgcCollection();
  virtual void add_igc
    (const boost::shared_ptr<EcostressImageGroundConnection>& Igc);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressIgcCollection")

