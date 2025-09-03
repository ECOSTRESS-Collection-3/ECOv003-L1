#ifndef ECOSTRESS_ORBIT_OFFSET_CORRECTION_H
#define ECOSTRESS_ORBIT_OFFSET_CORRECTION_H
#include "geocal/orbit_offset_correction.h"
#include <boost/make_shared.hpp>

namespace Ecostress {
/****************************************************************//**
   This is similar to a OrbitOffsetCorrection, but we have this
   set up to hold the attitude correction constant over a scene
*******************************************************************/
class EcostressOrbitOffsetCorrection : public GeoCal::Orbit {
public:
  EcostressOrbitOffsetCorrection(const boost::shared_ptr<GeoCal::Orbit> Orb_uncorr)
    : orb_corr(boost::make_shared<GeoCal::OrbitOffsetCorrection>(Orb_uncorr))
  {}
  virtual ~EcostressOrbitOffsetCorrection() {}

//-----------------------------------------------------------------------
/// The uncorrected orbit.
//-----------------------------------------------------------------------

  boost::shared_ptr<GeoCal::Orbit> orbit_uncorrected() const 
  { return orb_corr->orbit_uncorrected(); }
  
  virtual boost::shared_ptr<GeoCal::OrbitData> orbit_data(GeoCal::Time T) const
  { return orb_corr->orbit_data(T); }
  virtual boost::shared_ptr<GeoCal::OrbitData> 
  orbit_data(const GeoCal::TimeWithDerivative& T) const
  { return orb_corr->orbit_data(T); }
  void add_scene(int Scene_number, GeoCal::Time& Tstart, GeoCal::Time& Tend);
  std::vector<int> scene_list() const;
  virtual GeoCal::ArrayAd<double, 1> parameter_with_derivative() const;
  virtual void parameter_with_derivative(const GeoCal::ArrayAd<double, 1>& Parm);
  virtual std::vector<std::string> parameter_name() const;
  virtual blitz::Array<bool, 1> parameter_mask() const;
  virtual void print(std::ostream& Os) const;
  struct CorrData {
    GeoCal::Time tstart;
    GeoCal::Time tend;
    int scene_number;
    GeoCal::ArrayAd<double, 1> ypr_corr;
    template<class Archive>
    void serialize(Archive & ar, const unsigned int version);
  };
protected:
  virtual void notify_update()
  {
    notify_update_do(*this);
  }
private:
  std::map<int, CorrData> att_corr;
  boost::shared_ptr<GeoCal::OrbitOffsetCorrection> orb_corr;
  EcostressOrbitOffsetCorrection() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressOrbitOffsetCorrection);
BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressOrbitOffsetCorrection::CorrData);
#endif
