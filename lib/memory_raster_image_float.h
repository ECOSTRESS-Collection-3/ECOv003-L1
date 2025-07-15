#ifndef MEMORY_RASTER_IMAGE_FLOAT_H
#define MEMORY_RASTER_IMAGE_FLOAT_H
#include "geocal/raster_image_variable.h"
#include <blitz/array.h>
#include <vector>

namespace Ecostress {
/****************************************************************//**
  Variation of MemoryRasterImage that stores data as float.
*******************************************************************/

class MemoryRasterImageFloat : public GeoCal::RasterImageVariable {
public:
//-----------------------------------------------------------------------
/// Construct a MemoryRasterImage of the given size.
//-----------------------------------------------------------------------

  MemoryRasterImageFloat(int Number_line = 0, int Number_sample = 0)
    : RasterImageVariable(Number_line, Number_sample),
      data_(Number_line, Number_sample)
    {
    }

  virtual ~MemoryRasterImageFloat() {}

//-----------------------------------------------------------------------
/// Underlying data.
//-----------------------------------------------------------------------

  blitz::Array<double, 2>& data() {return  data_;}

//-----------------------------------------------------------------------
/// Underlying data.
//-----------------------------------------------------------------------

  const blitz::Array<double, 2>& data() const {return  data_;}

  virtual int unchecked_read(int Line, int Sample) const
  {
    return (int) data_(Line,Sample);
  }
  virtual double unchecked_read_double(int Line, int Sample) const
  {
    return data_(Line,Sample);
  }
  virtual void read_ptr(int Lstart, int Sstart, int Number_line, 
			int Number_sample, int* Res) const
  {
    range_check(Lstart, 0, number_line() - (Number_line - 1));
    range_check(Sstart, 0, number_sample() - (Number_sample - 1));
    for(int i = Lstart; i < Lstart + Number_line; ++i)
      for(int j = Sstart; j < Sstart + Number_sample; ++j, ++Res)
	*Res = (int) data_(i,j);
  }
  virtual void unchecked_write(int Line, int Sample, int Val)
  {
    data_(Line, Sample) = Val;
  }
  virtual void unchecked_write(int Line, int Sample, double Val)
  {
    data_(Line, Sample) = Val;
  }
  virtual void write(int Lstart, int Sstart, const blitz::Array<int, 2>& A);
  virtual void write(int Lstart, int Sstart, const blitz::Array<double, 2>& A);
  virtual void print(std::ostream& Os) const;
  virtual blitz::Array<double, 2> read_double(int Lstart, int Sstart, int Nline, 
					      int Nsamp) const;
private:
  blitz::Array<double, 2> data_; ///< Underlying data.
};
}

#endif
