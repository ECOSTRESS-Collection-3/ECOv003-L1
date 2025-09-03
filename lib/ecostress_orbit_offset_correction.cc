#include "ecostress_orbit_offset_correction.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
#include <algorithm>
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressOrbitOffsetCorrection::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(Orbit)
    & GEOCAL_NVP(att_corr)
    & GEOCAL_NVP(orb_corr);
}

template<class Archive>
void EcostressOrbitOffsetCorrection::CorrData::serialize(Archive & ar, const unsigned int version)
{
  ar & GEOCAL_NVP(tstart)
    & GEOCAL_NVP(tend)
    & GEOCAL_NVP(scene_number)    
    & GEOCAL_NVP(ypr_corr);
}

ECOSTRESS_IMPLEMENT(EcostressOrbitOffsetCorrection::CorrData);
ECOSTRESS_IMPLEMENT(EcostressOrbitOffsetCorrection);

//-----------------------------------------------------------------------
/// Add breakpoints for a given scene, with the given time range
/// for the scene.
//-----------------------------------------------------------------------

void EcostressOrbitOffsetCorrection::add_scene
(int Scene_number, GeoCal::Time& Tstart, GeoCal::Time& Tend)
{
  // To fill in
  notify_update();
}

//-----------------------------------------------------------------------
/// Return the list of scenes we have breakpoint for.
//-----------------------------------------------------------------------

std::vector<int> EcostressOrbitOffsetCorrection::scene_list() const
{
  std::vector<int> res;
  for(const auto& kv : att_corr)
    res.push_back(kv.first);
  return res;
}

ArrayAd<double, 1> EcostressOrbitOffsetCorrection::parameter_with_derivative() const
{
  // To fill in
  return orb_corr->parameter_with_derivative();
}

void EcostressOrbitOffsetCorrection::parameter_with_derivative(const ArrayAd<double, 1>& Parm)
{
  // To fill in
  orb_corr->parameter_with_derivative(Parm);
  notify_update();
}

std::vector<std::string> EcostressOrbitOffsetCorrection::parameter_name() const
{
  std::vector<std::string> res;
  for(const auto& kv : att_corr) {
    res.push_back("Yaw correction scene " + std::to_string(kv.first) + " (arcseconds)");
    res.push_back("Pitch correction scene " + std::to_string(kv.first) + " (arcseconds)");
    res.push_back("Roll correction scene " + std::to_string(kv.first) + " (arcseconds)");
  }
  return res;
}

blitz::Array<bool, 1> EcostressOrbitOffsetCorrection::parameter_mask() const
{
  blitz::Range ra = blitz::Range::all();
  blitz::Array<bool, 1> res(3 * att_corr.size());
  // For now, just have everything fitted
  res(ra) = true;
  return res;
}

void EcostressOrbitOffsetCorrection::print(std::ostream& Os) const
{
  Os << "EcostressOrbitOffsetCorrection";
}
