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
  {
  }
  virtual ~CombineOrbit() {}

//-------------------------------------------------------------------------
/// Add an orbit to the list
//-------------------------------------------------------------------------

  void add_orbit(const boost::shared_ptr<GeoCal::Orbit>& orb)
  {
    orb_list_.push_back(orb);
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
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::CombineOrbit);
#endif

