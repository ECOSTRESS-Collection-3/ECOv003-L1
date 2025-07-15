#include "memory_raster_image_float.h"
using namespace Ecostress;
using namespace GeoCal;

void MemoryRasterImageFloat::print(std::ostream& Os) const
{
  Os << "RasterImage of " << number_line() << " x " << number_sample() 
     << " all in memory, double type\n";
}


blitz::Array<double, 2> MemoryRasterImageFloat::read_double
(int Lstart, int Sstart, int Nline, int Nsamp) const
{
  if(Lstart < 0 || Lstart + Nline > number_line() ||
     Sstart < 0 || Sstart + Nsamp > number_sample()) {
    GeoCal::Exception e;
    e << "Data out of range in MemoryRasterImageFloat::read_double\n"
      << "  Lstart: " << Lstart << "\n"
      << "  Sstart: " << Sstart << "\n"
      << "  Nline:  " << Nline << "\n"
      << "  Nsamp:  " << Nsamp << "\n"
      << "  Raster number line: " << number_line() << "\n"
      << "  Raster number sample: " << number_sample() << "\n"
      << "  Underlying raster image: \n" << *this << "\n";
    throw e;
  }
  blitz::Array<double, 2> res(Nline, Nsamp);
  for(int i = 0; i < Nline; ++i)
    for(int j = 0; j < Nsamp; ++j)
      res(i,j) = data_(i+Lstart,j+Sstart);
  return res;
}

void MemoryRasterImageFloat::write(int Lstart, int Sstart, const blitz::Array<int, 2>& A)
{
  if(Lstart < 0 || Lstart + A.rows() > number_line() ||
     Sstart < 0 || Sstart + A.cols() > number_sample()) {
    GeoCal::Exception e;
    e << "Data out of range in MemoryRasterImageFloat::read_double\n"
      << "  Lstart: " << Lstart << "\n"
      << "  Sstart: " << Sstart << "\n"
      << "  Nline:  " << A.rows() << "\n"
      << "  Nsamp:  " << A.cols() << "\n"
      << "  Raster number line: " << number_line() << "\n"
      << "  Raster number sample: " << number_sample() << "\n"
      << "  Underlying raster image: \n" << *this << "\n";
    throw e;
  }
  for(int i = 0; i < A.rows(); ++i)
    for(int j = 0; j < A.cols(); ++j)
      data_(i+Lstart,j+Sstart) = A(i,j);
}

void MemoryRasterImageFloat::write(int Lstart, int Sstart, const blitz::Array<double, 2>& A)
{
  if(Lstart < 0 || Lstart + A.rows() > number_line() ||
     Sstart < 0 || Sstart + A.cols() > number_sample()) {
    GeoCal::Exception e;
    e << "Data out of range in MemoryRasterImageFloat::read_double\n"
      << "  Lstart: " << Lstart << "\n"
      << "  Sstart: " << Sstart << "\n"
      << "  Nline:  " << A.rows() << "\n"
      << "  Nsamp:  " << A.cols() << "\n"
      << "  Raster number line: " << number_line() << "\n"
      << "  Raster number sample: " << number_sample() << "\n"
      << "  Underlying raster image: \n" << *this << "\n";
    throw e;
  }
  for(int i = 0; i < A.rows(); ++i)
    for(int j = 0; j < A.cols(); ++j)
      data_(i+Lstart,j+Sstart) = A(i,j);
}  
