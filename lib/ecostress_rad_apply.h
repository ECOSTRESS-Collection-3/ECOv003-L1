#ifndef ECOSTRESS_RAD_APPLY_H
#define ECOSTRESS_RAD_APPLY_H
#include "geocal/calc_raster.h"

namespace Ecostress {
/****************************************************************//**
  This is a simple CalcRaster that applies gain and offset, and
  handles bad values. This can easily be done in python, but we need
  a CalcRaster to pass to GeometricModelImage, so it is easier to copy
  this little bit of code into C++.

  Just so we don't need special handling, we handle the case of Band =
  0 (This is SW band). For this band, we don't
  have a gain or offset to apply.

  We propagate bad pixels through as -9999.
*******************************************************************/

class EcostressRadApply : public GeoCal::CalcRaster {
public:
  EcostressRadApply(const std::string& Dn_fname, const std::string& Gain_fname,
		    int Band);
  virtual ~EcostressRadApply() {};
  int band() const {return band_;}
protected:
  virtual void calc(int Lstart, int Sstart) const;
private:
  int band_;
  boost::shared_ptr<RasterImage> dn, gain, offset;
  EcostressRadApply() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}
BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressRadApply);
#endif
