#ifndef COMBINE_ORBIT_H
#define COMBINE_ORBIT_H
#include "geocal/orbit.h"

namespace Ecostress {
/****************************************************************//**
  This combines multiple orbits into one virtual orbit.

  This should perhaps be moved over to GeoCal at some point.
*******************************************************************/

class CombineOrbit : public GeoCal::Orbit {
public:
//-------------------------------------------------------------------------
/// Constructor.
//-------------------------------------------------------------------------
  CombineOrbit()
    : last_used_index_(-1), is_sorted_(true)  // Empty list is trivially sorted
  {
  }
  virtual ~CombineOrbit() {}

//-------------------------------------------------------------------------
/// Add an orbit to the list
///
/// IMPORTANT: Orbits must have disjoint (non-overlapping) time ranges.
/// This function validates the disjoint property and throws an exception
/// if a new orbit overlaps with any existing orbit.
//-------------------------------------------------------------------------

  void add_orbit(const boost::shared_ptr<GeoCal::Orbit>& orb)
  {
    // Check for overlap with existing orbits (validate disjoint invariant)
    for(const auto& existing : orb_list_) {
      // Orbits overlap if neither is completely before the other
      bool disjoint = (orb->max_time() <= existing->min_time()) ||
                      (existing->max_time() <= orb->min_time());
      if(!disjoint) {
        GeoCal::Exception e;
        e << "Cannot add orbit with time range ["
          << orb->min_time() << ", " << orb->max_time()
          << ") - overlaps with existing orbit ["
          << existing->min_time() << ", " << existing->max_time() << ")";
        throw e;
      }
    }

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

//-------------------------------------------------------------------------
/// List of orbits  
//-------------------------------------------------------------------------

  const std::vector<boost::shared_ptr<GeoCal::Orbit> > & orbit_list() const
  {return orb_list_;}

    
  virtual boost::shared_ptr<GeoCal::OrbitData> orbit_data(GeoCal::Time T) const;
  virtual boost::shared_ptr<GeoCal::OrbitData>
  orbit_data(const GeoCal::TimeWithDerivative& T) const;
  virtual void print(std::ostream& Os) const;
private:
  std::vector<boost::shared_ptr<Orbit> > orb_list_;
  mutable int last_used_index_;           ///< Cache last successful orbit index
  mutable boost::shared_ptr<Orbit> last_used_orbit_;  ///< Cache pointer for temporal locality
  mutable bool is_sorted_;                ///< Track if list is sorted by min_time

//-------------------------------------------------------------------------
/// Ensure orbit list is sorted by min_time (lazy sorting)
//-------------------------------------------------------------------------
  void ensure_sorted() const;

  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::CombineOrbit);
#endif

