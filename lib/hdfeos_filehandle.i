// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "hdfeos_filehandle.h"
%}

%geocal_base_import(generic_object)
%ecostress_shared_ptr(Ecostress::HdfEosFileHandle);

namespace Ecostress {
class HdfEosFileHandle : public GeoCal::GenericObject {
public:
  enum { READ = 0, READWRITE = 1, TRUNC= 2, CREATE=0x0010u};
  HdfEosFileHandle(const std::string& Fname, int mode=READ);
  void close();
  %python_attribute(file_name, std::string);
  %python_attribute(mode, int);
  %python_attribute(file_id, hid_t);
  %python_attribute(grid_name, std::vector<std::string>);
  std::string print_to_string() const;
};
}

// List of things "import *" will include.
%python_export("HdfEosFileHandle")
