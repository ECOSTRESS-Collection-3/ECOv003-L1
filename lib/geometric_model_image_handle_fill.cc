#include "geometric_model_image_handle_fill.h"
#include "geocal/ostream_pad.h"
#include "ecostress_serialize_support.h"
using namespace Ecostress;
using namespace blitz;

template<class Archive>
void GeometricModelImageHandleFill::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(CalcRaster)
    & GEOCAL_NVP_(fill_value) & GEOCAL_NVP_(raw_data)
    & GEOCAL_NVP(model);
}


ECOSTRESS_IMPLEMENT(GeometricModelImageHandleFill);

// Print to stream.
void GeometricModelImageHandleFill::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "GeometricModelImageHandleFill\n"
     << "  number line: " << number_line() << "\n"
     << "  number sample: " << number_sample() << "\n"
     << "  geometric model:\n";
  opad << *model << "\n";
  opad.strict_sync();
  Os << "  underlying raster: \n";
  opad << *raw_data_ << "\n";
  opad.strict_sync();
}

// See base class for description
void GeometricModelImageHandleFill::calc(int Lstart, int Sstart) const
{
  for(int i = 0; i < data.rows(); ++i)
    for(int j = 0; j < data.cols(); ++j) {
      GeoCal::ImageCoordinate ic =
	model->original_image_coordinate(GeoCal::ImageCoordinate(i + Lstart, 
								 j + Sstart));
      if(ic.line < 0 || ic.line >= raw_data_->number_line() - 1 ||
	 ic.sample < 0 || ic.sample >= raw_data_->number_sample() - 1)
	data(i,j) = fill_value_;
      else {
	int i2 = (int) ic.line;
	int j2 = (int) ic.sample;
	double t1 = unchecked_read_double(i2, j2);
	double t2 = unchecked_read_double(i2, j2 + 1);
	double t3 = unchecked_read_double(i2 + 1, j2);
	double t4 = unchecked_read_double(i2 + 1, j2 + 1);
	if(t1 < fill_value_threshold) {
	  data(i,j) = t1;
	} else {
	  if(t2 < fill_value_threshold) {
	    data(i,j) = t2;
	  } else {
	    if(t3 < fill_value_threshold) {
	      data(i,j) = t3;
	    } else {
	      if(t4 < fill_value_threshold) {
		data(i,j) = t4;
	      } else {
		double t5 = t1 + (t2 - t1) * (ic.sample - j2);
		double t6 = t3 + (t4 - t3) * (ic.sample - j2);
		data(i, j) = t5 + (t6 - t5) * (ic.line - i2);
	      }
	    }
	  }
	}
      }
    }
}
