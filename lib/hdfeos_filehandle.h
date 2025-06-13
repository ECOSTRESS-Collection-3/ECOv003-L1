#ifndef HDFEOS_FILEHANDLE_H
#define HDFEOS_FILEHANDLE_H
#include "geocal/printable.h"
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
*******************************************************************/
  
class HdfEosFileHandle : public GeoCal::Printable<HdfEosFileHandle> {
public:
  enum { READ = 0, READWRITE = 1, TRUNC= 2 };
  HdfEosFileHandle(const std::string& Fname, int mode=READ);
  virtual ~HdfEosFileHandle() {close();}

//-----------------------------------------------------------------------
/// Close the file
//-----------------------------------------------------------------------
  
  void close();

//-----------------------------------------------------------------------
/// Filename of file
//-----------------------------------------------------------------------
  
  const std::string& filename() const {return fname_;}


//-----------------------------------------------------------------------
/// Mode file was opened with
//-----------------------------------------------------------------------
  
  int mode() const { return mode_;}

//-----------------------------------------------------------------------
/// File id
//-----------------------------------------------------------------------
  
  hid_t file_id() const { return gdfid_;}

  void print(std::ostream& Os) const;
private:
  std::string fname_;
  int mode_;
  hid_t gdfid_;
};
}
#endif
