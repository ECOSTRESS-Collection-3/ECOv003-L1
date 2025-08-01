#include "hdfeos_filehandle.h"
#include <geocal/geocal_exception.h>
#include <iostream>
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
  if(mode == TRUNC || mode == CREATE)
    // No grids yet, so skip trying to read.
    return;
  long bufsize;
  long ngrid = HE5_GDinqgrid(fname.c_str(), 0, &bufsize);
  if(ngrid == -1)
    // Ok if it fails, just skip
    return;
  if(bufsize > 0) {
    std::vector<char> buf(bufsize);
    ngrid = HE5_GDinqgrid(fname.c_str(), &buf[0], &bufsize);
    if(ngrid == -1)
      throw Exception("Call to HE5_GDinqgrid failed");
    if(buf[0] != '\0') {
      int st = 0;
      for(int i = 0; i < bufsize; ++i)
	if(buf[i] == ',') {
	  grid_name_.push_back(std::string(&buf[st], i-st));
	  st = i+1;
	}
      grid_name_.push_back(std::string(&buf[st], bufsize-st));
    }
  }
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
