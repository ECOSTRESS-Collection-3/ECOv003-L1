#ifndef HDFEOS_FILEHANDLE_H
#define HDFEOS_FILEHANDLE_H
#include "geocal/printable.h"
#include <vector>
extern "C" {
#include <HE5_HdfEosDef.h>
}

namespace Ecostress {
/****************************************************************//**
  Surprisingly, there doesn't seem to be a python library for
  reading and writing HDFEOS5. GDAL has limited read support, but
  can't generate these files. I wouldn't have necessarily selected
  this for the grid products, HDFEOS5 never really seemed to have
  very wide use. But this has already been done, so we will just
  provide support here.

  This is a pretty minimal set of classes, really just what is
  needed for generate the L1_CG product.

  Note that we allow fields to be created, but don't provide any
  access to the actual data. This is because we create fields in
  python, and h5py is already a complete library. We don't need to
  duplicate the functionality. We really just want to use HDFEOS to
  create the map projection stuff, and then fall back to h5py to do
  all the reading/writing.
  
  Similarly, we don't provide access to any attributes, again because
  h5py already had this.
*******************************************************************/
  
class HdfEosFileHandle : public GeoCal::Printable<HdfEosFileHandle> {
public:
  enum { READ = 0, READWRITE = 1, TRUNC= 2, CREATE=0x0010u};
  HdfEosFileHandle(const std::string& Fname, int mode=READ);
  virtual ~HdfEosFileHandle() {close();}

//-----------------------------------------------------------------------
/// Close the file
//-----------------------------------------------------------------------
  
  void close();

//-----------------------------------------------------------------------
/// Filename of file
//-----------------------------------------------------------------------
  
  const std::string& file_name() const {return fname_;}


//-----------------------------------------------------------------------
/// Mode file was opened with
//-----------------------------------------------------------------------
  
  int mode() const { return mode_;}

//-----------------------------------------------------------------------
/// Grid names in the file
//-----------------------------------------------------------------------
  
  const std::vector<std::string>& grid_name() const { return grid_name_;}
  
//-----------------------------------------------------------------------
/// File id
//-----------------------------------------------------------------------
  
  hid_t file_id() const { return gdfid_;}

  void print(std::ostream& Os) const;
private:
  std::string fname_;
  int mode_;
  hid_t gdfid_;
  std::vector<std::string> grid_name_;
};
}
#endif
