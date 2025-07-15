// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "memory_raster_image_float.h"
#include "geocal/image_ground_connection.h"
%}

%base_import(raster_image_variable)

%ecostress_shared_ptr(Ecostress::MemoryRasterImageFloat);
namespace Ecostress {
class MemoryRasterImageFloat : public GeoCal::RasterImageVariable {
public:
  MemoryRasterImageFloat(int Number_line = 0, int Number_sample = 0);
  virtual void write(int Lstart, int Sstart, const blitz::Array<int, 2>& A);
  virtual void write(int Lstart, int Sstart, const blitz::Array<double, 2>& A);
  %python_attribute(data, blitz::Array<double, 2>);
};
}

// List of things "import *" will include
%python_export("MemoryRasterImageFloat")
