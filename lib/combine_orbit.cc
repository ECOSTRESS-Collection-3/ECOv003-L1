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
  // Step 1: Find and classify overlaps with the new orbit
  std::vector<int> min_time_overlaps;  // Orbits that overlap new orbit's min_time
  std::vector<int> max_time_overlaps;  // Orbits that overlap new orbit's max_time

  for(size_t i = 0; i < orb_list_.size(); ++i) {
    bool overlaps = !(orb->max_time() <= orb_list_[i]->min_time() ||
                      orb_list_[i]->max_time() <= orb->min_time());
    if(!overlaps) continue;

    // Classify the type of overlap
    if(orb_list_[i]->min_time() < orb->min_time() &&
       orb_list_[i]->max_time() > orb->min_time()) {
      // Existing orbit overlaps new orbit's min_time
      min_time_overlaps.push_back(i);
    }

    if(orb_list_[i]->min_time() >= orb->min_time() &&
       orb_list_[i]->min_time() < orb->max_time()) {
      // Existing orbit overlaps new orbit's max_time
      max_time_overlaps.push_back(i);
    }
  }

  // Step 2: Validate constraint for new orbit - at most 1 overlap each end
  if(min_time_overlaps.size() > 1) {
    GeoCal::Exception e;
    e << "Cannot add orbit with time range ["
      << orb->min_time() << ", " << orb->max_time()
      << ") - has " << min_time_overlaps.size()
      << " overlaps at its min_time, maximum 1 allowed";
    throw e;
  }
  if(max_time_overlaps.size() > 1) {
    GeoCal::Exception e;
    e << "Cannot add orbit with time range ["
      << orb->min_time() << ", " << orb->max_time()
      << ") - has " << max_time_overlaps.size()
      << " overlaps at its max_time, maximum 1 allowed";
    throw e;
  }

  // Step 3: For each overlapping orbit, verify it doesn't exceed its limits
  // Check the orbit that overlaps new orbit's min_time
  if(min_time_overlaps.size() == 1) {
    int idx = min_time_overlaps[0];
    // This overlap is at existing orbit's max_time
    // Count how many orbits already overlap this existing orbit's max_time
    int max_time_overlap_count = 0;
    for(size_t i = 0; i < orb_list_.size(); ++i) {
      if((int)i == idx) continue;
      // Does orbit i overlap orbit[idx]'s max_time?
      if(orb_list_[i]->min_time() >= orb_list_[idx]->min_time() &&
         orb_list_[i]->min_time() < orb_list_[idx]->max_time()) {
        max_time_overlap_count++;
      }
    }
    if(max_time_overlap_count >= 1) {
      GeoCal::Exception e;
      e << "Cannot add orbit with time range ["
        << orb->min_time() << ", " << orb->max_time()
        << ") - existing orbit at index " << idx
        << " already has a max_time overlap";
      throw e;
    }
  }

  // Check the orbit that overlaps new orbit's max_time
  if(max_time_overlaps.size() == 1) {
    int idx = max_time_overlaps[0];
    // This overlap is at existing orbit's min_time
    // Count how many orbits already overlap this existing orbit's min_time
    int min_time_overlap_count = 0;
    for(size_t i = 0; i < orb_list_.size(); ++i) {
      if((int)i == idx) continue;
      // Does orbit i overlap orbit[idx]'s min_time?
      if(orb_list_[i]->min_time() < orb_list_[idx]->min_time() &&
         orb_list_[i]->max_time() > orb_list_[idx]->min_time()) {
        min_time_overlap_count++;
      }
    }
    if(min_time_overlap_count >= 1) {
      GeoCal::Exception e;
      e << "Cannot add orbit with time range ["
        << orb->min_time() << ", " << orb->max_time()
        << ") - existing orbit at index " << idx
        << " already has a min_time overlap";
      throw e;
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

  // Walk backwards from candidate to find earliest orbit containing T
  // Stop when we find an orbit with max_time <= T (no earlier orbit can contain T)
  for(auto it = candidate; ; --it) {
    if(T >= (*it)->min_time() && T < (*it)->max_time()) {
      // Found orbit containing T with earliest min_time
      last_used_orbit_ = *it;
      last_used_index_ = std::distance(orb_list_.begin(), it);
      return (*it)->orbit_data(T);
    }

    // If this orbit ends before T, no earlier orbit can contain T
    if((*it)->max_time() <= T) {
      break;
    }

    // Stop if we've reached the beginning
    if(it == orb_list_.begin()) {
      break;
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

  // Walk backwards from candidate to find earliest orbit containing T
  // Stop when we find an orbit with max_time <= T (no earlier orbit can contain T)
  for(auto it = candidate; ; --it) {
    if(T >= (*it)->min_time() && T < (*it)->max_time()) {
      // Found orbit containing T with earliest min_time
      last_used_orbit_ = *it;
      last_used_index_ = std::distance(orb_list_.begin(), it);
      return (*it)->orbit_data(T);
    }

    // If this orbit ends before T, no earlier orbit can contain T
    if((*it)->max_time() <= T) {
      break;
    }

    // Stop if we've reached the beginning
    if(it == orb_list_.begin()) {
      break;
    }
  }

  GeoCal::Exception e;
  e << "Time " << T << " not found in orbit list";
  throw e;
}

