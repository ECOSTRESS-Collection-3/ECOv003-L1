// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "coordinate_convert.h"
#include <geocal/camera.h>
#include <geocal/planet_coordinate.h>
%}
%geocal_base_import(ogr_coordinate)
namespace Ecostress {
  blitz::Array<double, 2> coordinate_convert(const blitz::Array<double, 1> latitude,
					     const blitz::Array<double, 1> longitude,
					     const boost::shared_ptr<GeoCal::OgrWrapper>& ogr);
}

// List of things "import *" will include
%python_export("coordinate_convert")
