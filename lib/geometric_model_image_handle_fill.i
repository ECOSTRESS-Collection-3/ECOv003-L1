// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "geometric_model_image_handle_fill.h"
#include "geocal/image_ground_connection.h"
#include "geocal/raster_image.h"
#include "geocal/geometric_model.h"  
%}
%geocal_base_import(calc_raster)
%import "geometric_model.i"
%ecostress_shared_ptr(Ecostress::GeometricModelImageHandleFill);

namespace Ecostress {
class GeometricModelImageHandleFill : public GeoCal::CalcRaster {
public:
  GeometricModelImageHandleFill(const boost::shared_ptr<GeoCal::RasterImage>& Data,
	 	      const boost::shared_ptr<GeoCal::GeometricModel>& Geom_model,
		      int Number_line, int Number_sample,
		      double Fill_value = 0.0);
  %python_attribute(raw_data, boost::shared_ptr<GeoCal::RasterImage>)
  %python_attribute(geometric_model, boost::shared_ptr<GeoCal::GeometricModel>)
  %python_attribute(fill_value, double)
  %pickle_serialization();
protected:
  virtual void calc(int Lstart, int Sstart) const;
};

}

// List of things "import *" will include
%python_export("GeometricModelImageHandleFill")
