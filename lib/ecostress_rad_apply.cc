#include "ecostress_rad_apply.h"
#include "ecostress_serialize_support.h"
#include "gdal_raster_image.h"
#include <boost/lexical_cast.hpp>
#include <boost/make_shared.hpp>

using namespace Ecostress;

template<class Archive>
void EcostressRadApply::serialize(Archive & ar,
				  const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(CalcRaster)
    & GEOCAL_NVP_(band) & GEOCAL_NVP(dn) & GEOCAL_NVP(gain)
    & GEOCAL_NVP(offset);
}

ECOSTRESS_IMPLEMENT(EcostressRadApply);

EcostressRadApply::EcostressRadApply
(const std::string& Dn_fname, const std::string& Gain_fname,
 int Band)
  : band_(Band)
{
  range_check(Band, 0, 6);
  if(Band != 0) {
    dn = boost::make_shared<GeoCal::GdalRasterImage>("HDF5:\"" + Dn_fname + "\"://UncalibratedDN/b" + boost::lexical_cast<std::string>(Band + 1) + "_image");
    gain = boost::make_shared<GeoCal::GdalRasterImage>("HDF5:\"" + Gain_fname + "\"://Gain/b" + boost::lexical_cast<std::string>(Band) + "_gain");
    offset = boost::make_shared<GeoCal::GdalRasterImage>("HDF5:\"" + Gain_fname + "\"://Offset/b" + boost::lexical_cast<std::string>(Band) + "_offset");
  } else {
    dn = boost::make_shared<GeoCal::GdalRasterImage>("HDF5:\"" + Gain_fname + "\"://SWIR/b6_dcc");
  }
  number_line_ = dn->number_line();
  number_sample_ = dn->number_sample();
  number_tile_line_ = 256;
  number_tile_sample_ = number_sample_;
}

void EcostressRadApply::calc(int Lstart, int Sstart) const
{
  using namespace blitz;
  Array<int, 2> dnd = dn->read(Lstart, Sstart, data.rows(), data.cols());
  if(gain) {
    Array<double, 2> gaind = gain->read_double(Lstart, Sstart,
					    data.rows(), data.cols());
    Array<double, 2> offsetd = offset->read_double(Lstart, Sstart,
						  data.rows(), data.cols());
    data = where(dnd < 0 || gaind < -9998 || offsetd < -9998,
		 -9999.0,
		 dnd * gaind + offsetd);
  } else
    data = where(dnd < 0, -9999.0, cast<double>(dnd));
}
