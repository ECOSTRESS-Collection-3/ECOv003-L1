#include "ecostress_rad_average.h"
#include "ecostress_serialize_support.h"
#include "ecostress_dqi.h"

using namespace Ecostress;

template<class Archive>
void EcostressRadAverage::serialize(Archive & ar,
				  const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(CalcRaster)
    & GEOCAL_NVP_(raw_data);
}

ECOSTRESS_IMPLEMENT(EcostressRadAverage);

EcostressRadAverage::EcostressRadAverage
(const boost::shared_ptr<GeoCal::RasterImage>& Original_data)
  : raw_data_(Original_data)
{
  number_line_ = raw_data_->number_line() / 2;
  number_sample_ = raw_data_->number_sample();
  number_tile_line_ = 128;
  number_tile_sample_ = number_sample_;
}

void EcostressRadAverage::calc(int Lstart, int Sstart) const
{
  using namespace blitz;
  Array<double, 2> raw = raw_data_->read_double(Lstart * 2, Sstart,
						data.rows() * 2, data.cols());
  for(int i = 0; i < data.rows(); ++i)
    for(int j = 0; j < data.cols(); ++j) {
      double v1 = raw(2*i,j);
      double v2 = raw(2*i+1,j);
      if(v1 <= fill_value_threshold) {
	if(v2 <= fill_value_threshold)
	  data(i,j) = std::max(v1, v2);
	else
	  data(i,j) = v2;
      } else {
	if(v2 <= fill_value_threshold)
	  data(i,j) = v1;
	else
	  data(i,j) = (v1 + v2) / 2;
      }
    }
}
