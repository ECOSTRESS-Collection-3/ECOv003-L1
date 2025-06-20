#include "geometric_model_image_handle_fill.h"
#include "ecostress_dqi.h"
#include "geocal/ostream_pad.h"
#include "ecostress_serialize_support.h"
#include <algorithm>
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
      if(ic.line - 1 < 0 || ic.line >= raw_data_->number_line() ||
	 ic.sample - 1 < 0 || ic.sample >= raw_data_->number_sample())
	data(i,j) = fill_value_;
      else {
      	int ln = (int) floor(ic.line + 0.5);
	int smp = (int) floor(ic.sample + 0.5);
	// Grab fill values by nearest neighbor, since we can't really
	// do bilinear interpolation of fill values
	if(ln < 0 || ln >= raw_data_->number_line() ||
	   smp < 0 || smp >= raw_data_->number_sample())
	  data(i,j) = fill_value_;
	else {
	  double v = raw_data_->unchecked_read_double(ln, smp);
	  if(v < fill_value_threshold) {
	    data(i, j) = v;
	  } else {
	    // If we aren't using a fill value, then do bilinear interpolation
	    int i2 = (int) ic.line;
	    int j2 = (int) ic.sample;
	    // We don't want to fail at the edge, so special handling
	    // there. We allow a slight extrapolation, rather than doing
	    // interpolation
	    if(i2 < 0)
	      i2 +=1;
	    if(j2 < 0)
	      j2 +=1;
	    if(i2+1 >= raw_data_->number_line())
	      i2 -=1;
	    if(j2+1 >= raw_data_->number_sample())
	      j2 -=1;
	    double t1 = raw_data_->unchecked_read_double(i2, j2);
	    double t2 = raw_data_->unchecked_read_double(i2, j2 + 1);
	    double t3 = raw_data_->unchecked_read_double(i2 + 1, j2);
	    double t4 = raw_data_->unchecked_read_double(i2 + 1, j2 + 1);
	    double mint = min(t1,min(t2,min(t3,t4)));
	    if(mint < fill_value_threshold) {
	      // Handling in case at least one of the values are
	      // fill. We replace the fill value with the average to
	      // get a reasonable value for the interpolation
	      double sum = 0;
	      double count = 0;
	      if(t1 > fill_value_threshold) {
		sum += t1;
		count++;
	      }
	      if(t2 > fill_value_threshold) {
		sum += t2;
		count++;
	      }
	      if(t3 > fill_value_threshold) {
		sum += t3;
		count++;
	      }
	      if(t4 > fill_value_threshold) {
		sum += t4;
		count++;
	      }
	      double avg;
	      if(count > 0)
		avg = sum / count;
	      else
		avg = mint;
	      if(t1 < fill_value_threshold)
		t1 = avg;
	      if(t2 < fill_value_threshold)
		t2 = avg;
	      if(t3 < fill_value_threshold)
		t3 = avg;
	      if(t4 < fill_value_threshold)
		t4 = avg;
	    }
	    double t5 = t1 + (t2 - t1) * (ic.sample - j2);
	    double t6 = t3 + (t4 - t3) * (ic.sample - j2);
	    data(i, j) = t5 + (t6 - t5) * (ic.line - i2);
	  }
	}
      }
    }
}
