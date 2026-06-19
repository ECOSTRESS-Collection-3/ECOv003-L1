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

/// Add an orbit to the list - see header for full documentation
void CombineOrbit::add_orbit(const boost::shared_ptr<GeoCal::Orbit>& orb)
{
  // Step 1: Find which existing orbits overlap with the new orbit
  std::vector<int> overlapping_indices;
  for(size_t i = 0; i < orb_list_.size(); ++i) {
    bool overlaps = !(orb->max_time() <= orb_list_[i]->min_time() ||
                      orb_list_[i]->max_time() <= orb->min_time());
    if(overlaps) {
      overlapping_indices.push_back(i);
    }
  }

  // Step 2: Validate constraint - at most one overlap allowed
  if(overlapping_indices.size() > 1) {
    GeoCal::Exception e;
    e << "Cannot add orbit with time range ["
      << orb->min_time() << ", " << orb->max_time()
      << ") - overlaps with " << overlapping_indices.size() << " existing orbits. "
      << "Each orbit may overlap with at most one other orbit.";
    throw e;
  }

  // Step 3: If there's one overlap, verify that orbit doesn't already
  // overlap with any OTHER existing orbit
  if(overlapping_indices.size() == 1) {
    int overlap_idx = overlapping_indices[0];
    for(size_t i = 0; i < orb_list_.size(); ++i) {
      if((int)i == overlap_idx) continue;  // Skip self

      bool already_overlaps =
        !(orb_list_[overlap_idx]->max_time() <= orb_list_[i]->min_time() ||
          orb_list_[i]->max_time() <= orb_list_[overlap_idx]->min_time());

      if(already_overlaps) {
        GeoCal::Exception e;
        e << "Cannot add orbit with time range ["
          << orb->min_time() << ", " << orb->max_time()
          << ") - it overlaps with existing orbit at index " << overlap_idx
          << " which already overlaps with orbit at index " << i
          << ". Each orbit may overlap with at most one other orbit.";
        throw e;
      }
    }
  }

  // All checks passed - add the orbit
  orb_list_.push_back(orb);

  // Update combined orbit's time range
  if(orb_list_.size() == 1) {
    min_tm = orb->min_time();
    max_tm = orb->max_time();
  } else {
    if(orb->min_time() < min_tm)
      min_tm = orb->min_time();
    if(orb->max_time() > max_tm)
      max_tm = orb->max_time();
  }

  // Mark as unsorted - will sort on first access
  is_sorted_ = false;

  // Invalidate cache
  last_used_index_ = -1;
  last_used_orbit_.reset();
}

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

  // Binary search: find first orbit with min_time > T
  auto upper = std::upper_bound(orb_list_.begin(), orb_list_.end(), T,
                                 [](Time t, const boost::shared_ptr<Orbit>& orb) {
                                   return t < orb->min_time();
                                 });

  // Candidate is the orbit just before upper
  if(upper == orb_list_.begin()) {
    GeoCal::Exception e;
    e << "Time " << T << " not found in orbit list";
    throw e;
  }

  auto candidate = std::prev(upper);

  // Check previous orbit first (earlier min_time, preferred on overlap)
  if(candidate != orb_list_.begin()) {
    auto prev = std::prev(candidate);
    if(T >= (*prev)->min_time() && T < (*prev)->max_time()) {
      last_used_orbit_ = *prev;
      last_used_index_ = std::distance(orb_list_.begin(), prev);
      return (*prev)->orbit_data(T);
    }
  }

  // Check candidate orbit
  if(T >= (*candidate)->min_time() && T < (*candidate)->max_time()) {
    last_used_orbit_ = *candidate;
    last_used_index_ = std::distance(orb_list_.begin(), candidate);
    return (*candidate)->orbit_data(T);
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

  // Binary search: find first orbit with min_time > T
  auto upper = std::upper_bound(orb_list_.begin(), orb_list_.end(), T,
                                 [](const TimeWithDerivative& t,
                                    const boost::shared_ptr<Orbit>& orb) {
                                   return t < orb->min_time();
                                 });

  // Candidate is the orbit just before upper
  if(upper == orb_list_.begin()) {
    GeoCal::Exception e;
    e << "Time " << T << " not found in orbit list";
    throw e;
  }

  auto candidate = std::prev(upper);

  // Check previous orbit first (earlier min_time, preferred on overlap)
  if(candidate != orb_list_.begin()) {
    auto prev = std::prev(candidate);
    if(T >= (*prev)->min_time() && T < (*prev)->max_time()) {
      last_used_orbit_ = *prev;
      last_used_index_ = std::distance(orb_list_.begin(), prev);
      return (*prev)->orbit_data(T);
    }
  }

  // Check candidate orbit
  if(T >= (*candidate)->min_time() && T < (*candidate)->max_time()) {
    last_used_orbit_ = *candidate;
    last_used_index_ = std::distance(orb_list_.begin(), candidate);
    return (*candidate)->orbit_data(T);
  }

  GeoCal::Exception e;
  e << "Time " << T << " not found in orbit list";
  throw e;
}

