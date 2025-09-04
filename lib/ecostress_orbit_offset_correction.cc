#include "ecostress_orbit_offset_correction.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
#include <algorithm>
#include <set>
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
///
/// If Init_value_match is false, we initialize the offset to 0. If it
/// is true, then we match whatever the current correction we would
/// have calculated for Tstart + (Tend - Tstart) / 2.
//-----------------------------------------------------------------------

void EcostressOrbitOffsetCorrection::add_scene
(int Scene_number, GeoCal::Time& Tstart, GeoCal::Time& Tend, bool Init_value_match)
{
  if(att_corr.find(Scene_number) != att_corr.end()) {
    GeoCal::Exception e;
    e << "Already have scene " << Scene_number << " in map";
    throw e;
  }
  if(Tstart >= Tend)
    throw Exception("Tstart needs to be < Tend");
  att_corr[Scene_number] = CorrData(Scene_number, Tstart, Tend);
  if(Init_value_match)
    att_corr[Scene_number].ypr_corr = orb_corr->att_parm_to_match(Tstart + (Tend - Tstart) / 2);
  // We may have tstart already in the list, if we happen to have
  // added the previous scene. If so, offset slightly so we have a new
  // point (makes logic simpler if we don't need to worry about
  // handling common boundaries
  auto alist = orb_corr->attitude_time_point();
  std::set<Time> tmset(alist.begin(), alist.end());
  if(tmset.find(Tstart) == tmset.end())
    orb_corr->insert_attitude_time_point(Tstart);
  else
    orb_corr->insert_attitude_time_point(Tstart+1e-6);
  if(tmset.find(Tend) == tmset.end())
    orb_corr->insert_attitude_time_point(Tend);
  else
    orb_corr->insert_attitude_time_point(Tend-1e-6);
  // Set values in orb_corr
  parameter_with_derivative(parameter_with_derivative());
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
  blitz::Array<AutoDerivative<double>, 1> res(3 * att_corr.size());
  int i = 0;
  for(const auto& kv : att_corr) {
    auto cv = kv.second;
    res(i) = cv.ypr_corr(0);
    res(i+1) = cv.ypr_corr(1);
    res(i+2) = cv.ypr_corr(2);
    i += 3;
  }
  return res;
}

void EcostressOrbitOffsetCorrection::parameter_with_derivative(const ArrayAd<double, 1>& Parm)
{
  if(Parm.rows() != int(3 * att_corr.size())) {
    GeoCal::Exception e;
    e << "Expected parm size of " << 3 * att_corr.size() << " but was " << Parm.rows();
    throw e;
  }
  ArrayAd<double, 1> orb_corr_parm(6 * att_corr.size(), Parm.number_variable());
  int i = 0;
  int j = 0;
  for(auto& kv : att_corr) {
    kv.second.ypr_corr.resize_number_variable(Parm.number_variable());
    kv.second.ypr_corr = Parm(blitz::Range(i, i+2));
    i += 3;
    orb_corr_parm(j) = kv.second.ypr_corr(0);
    orb_corr_parm(j+1) = kv.second.ypr_corr(1);
    orb_corr_parm(j+2) = kv.second.ypr_corr(2);
    j+= 3;
    orb_corr_parm(j) = kv.second.ypr_corr(0);
    orb_corr_parm(j+1) = kv.second.ypr_corr(1);
    orb_corr_parm(j+2) = kv.second.ypr_corr(2);
    j+= 3;
  }
  orb_corr->parameter_with_derivative(orb_corr_parm);
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
  OstreamPad opad(Os, "    ");
  Os << "EcostressOrbitOffsetCorrection\n"
     << "  Underlying orbit:\n";
  opad << *orbit_uncorrected() << "\n";
  opad.strict_sync();
  std::vector<std::string> pname = parameter_name();
  blitz::Array<double, 1> parm = parameter();
  const static int sv_num_width = 17;
  for(int i = 0; i < parm.rows(); ++i)
    Os << "     " << std::setprecision(sv_num_width - 7) 
       << std::setw(sv_num_width) << parm(i) << "  "
       << pname[i] << "\n";
}
