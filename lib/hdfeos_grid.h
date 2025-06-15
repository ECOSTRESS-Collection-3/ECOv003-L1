#ifndef HDFEOS_GRID_H
#define HDFEOS_GRID_H
#include "hdfeos_filehandle.h"
#include <geocal/map_info.h>
#include <boost/shared_ptr.hpp>

namespace Ecostress {
/****************************************************************//**
  This handles a HDFEOS grid in a file.

  Note that we allow fields to be created, but don't provide any acces
  to the actual data in this class. This is because we create fields
  in python, and h5py is already a complete library. We don't need to
  duplicate the functionality. We really just want to use HDFEOS to
  create the map projection stuff, and then fall back to h5py to
  do all the reading/writing.

  Similarly, we don't provide access to any attributes, again because
  h5py already had this.
*******************************************************************/

class HdfEosGrid : public GeoCal::Printable<HdfEosGrid> {
public:
  HdfEosGrid(const boost::shared_ptr<HdfEosFileHandle>& Fhandle, const std::string& Grid_name);
  HdfEosGrid(const boost::shared_ptr<HdfEosFileHandle>& Fhandle, const std::string& Grid_name,
	     const GeoCal::MapInfo& Minfo, int Compression_type=HE5_HDFE_COMP_DEFLATE,
	     int Deflate_level=9);
  virtual ~HdfEosGrid() { close(); }

  static double dms_to_deg(double dms);
  static double deg_to_dms(double deg);
  
//-----------------------------------------------------------------------
/// Close the grid
//-----------------------------------------------------------------------
  
  void close();

//-----------------------------------------------------------------------
/// Grid name
//-----------------------------------------------------------------------

  const std::string& grid_name() const { return gname_; }

//-----------------------------------------------------------------------
/// File handle
//-----------------------------------------------------------------------

  const boost::shared_ptr<HdfEosFileHandle>& file_handle() const { return fhandle_; }

//-----------------------------------------------------------------------
/// Mapinfo for grid
//-----------------------------------------------------------------------

  const GeoCal::MapInfo& map_info() const { return minfo;}

//-----------------------------------------------------------------------
/// List of fields in grid
//-----------------------------------------------------------------------
  
  const std::vector<std::string>& field_name() const { return field_name_;}
  
//-----------------------------------------------------------------------
/// File id
//-----------------------------------------------------------------------
  
  hid_t grid_id() const { return gid_;}

  void add_field_uchar(const std::string& Name);
  void add_field_float(const std::string& Name);
  
  void print(std::ostream& Os) const;
private:
  boost::shared_ptr<HdfEosFileHandle> fhandle_;
  GeoCal::MapInfo minfo;
  std::string gname_;
  std::vector<std::string> field_name_;
  hid_t gid_;
  int compression_code, deflate_level;
};
}

#endif
