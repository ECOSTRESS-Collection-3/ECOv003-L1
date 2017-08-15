// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_rad_average.h"
%}
%geocal_base_import(calc_raster)
%ecostress_shared_ptr(Ecostress::EcostressRadAverage);
namespace Ecostress {
class EcostressRadAverage : public GeoCal::CalcRaster {
public:
  EcostressRadAverage(const boost::shared_ptr<GeoCal::RasterImage>&
		      Original_data);
  %python_attribute(raw_data, boost::shared_ptr<GeoCal::RasterImage>);
protected:
  virtual void calc(int Lstart, int Sstart) const;
  %pickle_serialization();
};
}

