#ifndef ECOSTRESS_RAD_AVERAGE_H
#define ECOSTRESS_RAD_AVARAGE_H
#include "geocal/calc_raster.h"

namespace Ecostress {
/****************************************************************//**
  This is GeoCal::RasterAveraged, but with additional logic added for
  handling bad pixels/missing data (values of -9999). When averaging
  we leave them out, unless both pixels we are averaging is -9999 in
  which case we give the results as -9999.
*******************************************************************/

class EcostressRadAverage : public GeoCal::CalcRaster {
public:
  EcostressRadAverage(const boost::shared_ptr<GeoCal::RasterImage>&
		      Original_data);
  virtual ~EcostressRadAverage() {}
  const boost::shared_ptr<GeoCal::RasterImage>& raw_data() const
  { return raw_data_; }
protected:
  virtual void calc(int Lstart, int Sstart) const;
private:
  boost::shared_ptr<GeoCal::RasterImage> raw_data_;
  EcostressRadAverage() {}
    friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}
BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressRadAverage);
#endif
