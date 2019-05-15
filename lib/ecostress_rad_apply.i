// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_rad_apply.h"
#include "geocal/image_ground_connection.h"
%}
%geocal_base_import(calc_raster)
%ecostress_shared_ptr(Ecostress::EcostressRadApply);
namespace Ecostress {
class EcostressRadApply : public GeoCal::CalcRaster {
public:
  EcostressRadApply(const std::string& Dn_fname, const std::string& Gain_fname,
		    int Band);
  %python_attribute(band, int);
protected:
  virtual void calc(int Lstart, int Sstart) const;
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressRadApply")
