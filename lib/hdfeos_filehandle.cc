#include "hdfeos_filehandle.h"
#include <geocal/geocal_exception.h>
using namespace Ecostress;
using namespace GeoCal;

//-------------------------------------------------------------------------
/// Constructor, open the file for reading, read/write, or
/// creating/truncating a file
//-------------------------------------------------------------------------

HdfEosFileHandle::HdfEosFileHandle(const std::string& fname, int mode)
  : fname_(fname),
    mode_(mode)
{
  gdfid_ = HE5_GDopen(fname.c_str(), mode);
  if(gdfid_ == -1)
    throw Exception("Trouble opening file " + fname);
}

void HdfEosFileHandle::close()
{
  if(gdfid_ != -1)
    HE5_GDclose(gdfid_);
  gdfid_ = -1;
}

void HdfEosFileHandle::print(std::ostream& Os) const
{
  Os << "HdfEosFileHandle\n"
     << "  Filename: " << fname_ << "\n"
     << "  Mode:     " << mode_ << "\n";
}
