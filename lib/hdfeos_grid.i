// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "hdfeos_grid.h"
%}

%geocal_base_import(generic_object)
%geocal_base_import(map_info)
%import "hdfeos_filehandle.i"
%ecostress_shared_ptr(Ecostress::HdfEosGrid);

namespace Ecostress {
class HdfEosGrid : public GeoCal::GenericObject {
public:
  HdfEosGrid(const boost::shared_ptr<HdfEosFileHandle>& Fhandle, const std::string& Grid_name);
  HdfEosGrid(const boost::shared_ptr<HdfEosFileHandle>& Fhandle, const std::string& Grid_name,
	     const GeoCal::MapInfo& Minfo);
  void close();
  static double dms_to_deg(double dms);
  static double deg_to_dms(double deg);
  %python_attribute(grid_name, std::string);
  %python_attribute(file_handle, boost::shared_ptr<HdfEosFileHandle>);
  %python_attribute(grid_id, hid_t);
  %python_attribute(map_info, GeoCal::MapInfo);
  %python_attribute(field_name, std::vector<std::string>);
  void add_field_uchar(const std::string& Name);
  void add_field_float(const std::string& Name);
  std::string print_to_string() const;
};
}

// List of things "import *" will include.
%python_export("HdfEosGrid")
