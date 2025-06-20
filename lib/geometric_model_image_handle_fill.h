#ifndef GEOMETRIC_MODEL_IMAGE_HANDLE_FILL_H
#define GEOMETRIC_MODEL_IMAGE_HANDLE_FILL_H
#include "geocal/calc_raster.h"
#include "geocal/geometric_model.h"

namespace Ecostress {
/****************************************************************//**
  Variation of GeoCal::GeometricModelImage that handles fill data. 
*******************************************************************/

class GeometricModelImageHandleFill : public GeoCal::CalcRaster {
public:
//-----------------------------------------------------------------------
/// Constructor. This takes underlying data, and a geometric model to
/// use to resample it.
///
/// Because we fill in data outside of the original image with O's
/// this image can be any size. So the size desired needs to be passed
/// in. 
//-----------------------------------------------------------------------

  GeometricModelImageHandleFill(const boost::shared_ptr<GeoCal::RasterImage>& Data,
				const boost::shared_ptr<GeoCal::GeometricModel>& Geom_model,
		      int Number_line, int Number_sample,
		      double Fill_value = 0.0)
    : CalcRaster(Number_line, Number_sample), 
      fill_value_(Fill_value),
      raw_data_(Data),
      model(Geom_model) {}
  virtual ~GeometricModelImageHandleFill() {}
  virtual void print(std::ostream& Os) const;
  double fill_value() const {return fill_value_;}
  const boost::shared_ptr<GeoCal::RasterImage>& raw_data() const {return raw_data_;}
  const boost::shared_ptr<GeoCal::GeometricModel>& geometric_model() const 
  {return model;}
protected:
  virtual void calc(int Lstart, int Sstart) const;
  GeometricModelImageHandleFill() {}
private:
  double fill_value_;
  boost::shared_ptr<GeoCal::RasterImage> raw_data_;
  boost::shared_ptr<GeoCal::GeometricModel> model;
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::GeometricModelImageHandleFill);
#endif
