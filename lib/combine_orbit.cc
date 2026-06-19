#include "combine_orbit.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"
#include <algorithm>  // For std::sort, std::upper_bound
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void CombineOrbit::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(Orbit)
    & GEOCAL_NVP_(orb_list);

  // On deserialization, reset transient cache and mark as unsorted
  if(Archive::is_loading::value) {
    last_used_index_ = -1;
    last_used_orbit_.reset();
    is_sorted_ = false;  // Will sort on first access
  }
}

ECOSTRESS_IMPLEMENT(CombineOrbit);

/// Ensure orbit list is sorted by min_time (lazy sorting)
void CombineOrbit::ensure_sorted() const
{
  if(!is_sorted_ && !orb_list_.empty()) {
    // Sort by min_time (const_cast needed for mutable operation)
    std::sort(const_cast<std::vector<boost::shared_ptr<Orbit>>&>(orb_list_).begin(),
              const_cast<std::vector<boost::shared_ptr<Orbit>>&>(orb_list_).end(),
              [](const boost::shared_ptr<Orbit>& a,
                 const boost::shared_ptr<Orbit>& b) {
                return a->min_time() < b->min_time();
              });
    const_cast<bool&>(is_sorted_) = true;
  }
}

/// See base class for description
void CombineOrbit::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "CombineOrbit\n";
  for(auto i : orb_list_)
    opad << *i << "\n";
}

/// See base class for description
boost::shared_ptr<OrbitData> CombineOrbit::orbit_data(Time T) const
{
  // Check empty list
  if(orb_list_.empty()) {
    GeoCal::Exception e;
    e << "Time " << T << " not found - orbit list is empty";
    throw e;
  }

  // Check cached orbit first (temporal locality optimization)
  if(last_used_orbit_ &&
     T >= last_used_orbit_->min_time() &&
     T < last_used_orbit_->max_time())
    return last_used_orbit_->orbit_data(T);

  // Ensure list is sorted for binary search
  ensure_sorted();

  // Binary search for orbit containing time T
  // Find first orbit where min_time > T, then back up one
  auto it = std::upper_bound(orb_list_.begin(), orb_list_.end(), T,
                             [](Time t, const boost::shared_ptr<Orbit>& orb) {
                               return t < orb->min_time();
                             });

  // upper_bound returns first element > T, we want the one before it
  if(it != orb_list_.begin()) {
    --it;
    // Verify T is actually in this orbit's range
    if(T >= (*it)->min_time() && T < (*it)->max_time()) {
      // Update cache
      last_used_index_ = std::distance(orb_list_.begin(), it);
      last_used_orbit_ = *it;
      return (*it)->orbit_data(T);
    }
  }

  GeoCal::Exception e;
  e << "Time " << T << " not found in orbit list";
  throw e;
}

boost::shared_ptr<GeoCal::OrbitData>
CombineOrbit::orbit_data(const GeoCal::TimeWithDerivative& T) const
{
  // Check empty list
  if(orb_list_.empty()) {
    GeoCal::Exception e;
    e << "Time " << T << " not found - orbit list is empty";
    throw e;
  }

  // Check cached orbit first
  if(last_used_orbit_ &&
     T >= last_used_orbit_->min_time() &&
     T < last_used_orbit_->max_time())
    return last_used_orbit_->orbit_data(T);

  // Ensure list is sorted
  ensure_sorted();

  // Binary search
  auto it = std::upper_bound(orb_list_.begin(), orb_list_.end(), T,
                             [](const TimeWithDerivative& t,
                                const boost::shared_ptr<Orbit>& orb) {
                               return t < orb->min_time();
                             });

  if(it != orb_list_.begin()) {
    --it;
    if(T >= (*it)->min_time() && T < (*it)->max_time()) {
      last_used_index_ = std::distance(orb_list_.begin(), it);
      last_used_orbit_ = *it;
      return (*it)->orbit_data(T);
    }
  }

  GeoCal::Exception e;
  e << "Time " << T << " not found in orbit list";
  throw e;
}

