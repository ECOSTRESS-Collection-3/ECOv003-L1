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
/// IMPORTANT: Each orbit may overlap with at most ONE other orbit.
/// When multiple orbits contain a time, the orbit with earliest min_time
/// is preferred. This function validates the single-overlap constraint
/// and throws an exception if violated.
//-------------------------------------------------------------------------

  void add_orbit(const boost::shared_ptr<GeoCal::Orbit>& orb);

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

