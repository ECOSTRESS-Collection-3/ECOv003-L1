#include "ecostress_orbit.h"
#include "ecostress_serialize_support.h"
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressOrbit::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(HdfOrbit_Eci_TimeJ2000)
    & GEOCAL_NVP_(large_gap)
    & GEOCAL_NVP_(pad);
}

ECOSTRESS_IMPLEMENT(EcostressOrbit);

/// See base class for description
void EcostressOrbit::print(std::ostream& Os) const
{
  Os << "EcostressOrbit\n"
     << "  File name:        " << file_name() << "\n"
     << "  Min time:         " << min_time() << "\n"
     << "  Max time:         " << max_time() << "\n"
     << "  Large gap:        " << large_gap() << " s\n"
     << "  Extrapolation pad: " << extrapolation_pad() << " s\n";
}


/// See base class for description
void EcostressOrbit::interpolate_or_extrapolate_data
(GeoCal::Time T, boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q1,
 boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q2) const
{
  range_check_inclusive(T, min_time(), max_time());
  time_map::iterator i = orbit_data_map.lower_bound(T);
  // Handle extrapolation past beginning of data
  if(i == orbit_data_map.end())
    i = orbit_data_map.lower_bound(orbit_data_map.rbegin()->first);
  check_lazy_evaluation(i);
  // Special handling if we are looking at the very first point
  if(i == orbit_data_map.begin() && T - i->first <= 0.0) {
    ++i;
    check_lazy_evaluation(i);
  }
  Q2 = i->second;
  --i;
  check_lazy_evaluation(i);
  Q1 = i->second;
  // Handling for large gaps
  if(Q2->time() - Q1->time() > large_gap_) {
    if(T - Q1->time() <= pad_ && i != orbit_data_map.begin()) {
      Q2 = Q1;
      --i;
      check_lazy_evaluation(i);
      Q1 = i->second;
      return;
    }
    ++i;
    if(Q2->time() - T <= pad_ && i != orbit_data_map.end()) {
      Q1 = Q2;
      ++i;
      check_lazy_evaluation(i);
      Q2 = i->second;
      return;
    }
    GeoCal::Exception e;
    e << "Request time is in the middle of a large gap:\n"
      << "  T:         " << T << "\n"
      << "  Gap start: " << Q1->time() << "\n"
      << "  Gap end:   " << Q2->time() << "\n";
    throw e;
  }
}


