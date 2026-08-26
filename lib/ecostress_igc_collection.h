#ifndef ECOSTRESS_IGC_COLLECTION_H
#define ECOSTRESS_IGC_COLLECTION_H
#include "ecostress_image_ground_connection.h"
#include "ecostress_image_ground_connection_subset.h"
#include "igc_array.h"

namespace Ecostress {
/****************************************************************//**
  This is a collection of EcostressImageGroundConnection. This is just
  a IgcArray, with a few convenience functions put in. 
*******************************************************************/

class EcostressIgcCollection : public virtual GeoCal::IgcArray {
public:
  EcostressIgcCollection()
  { assume_igc_independent_ = false; }
  virtual ~EcostressIgcCollection() {}
  const boost::shared_ptr<GeoCal::Orbit>& orbit() const;
  void orbit(const boost::shared_ptr<GeoCal::Orbit>& Orb);
  const boost::shared_ptr<GeoCal::Camera>& camera() const;
  void camera(const boost::shared_ptr<GeoCal::Camera>& Cam);
  virtual void add_igc(const boost::shared_ptr<GeoCal::ImageGroundConnection>& Igc)
  {
    auto igc1 = boost::dynamic_pointer_cast<EcostressImageGroundConnection>(Igc);
    auto igc2 = boost::dynamic_pointer_cast<EcostressImageGroundConnectionSubset>(Igc);
    if(!(igc1 || igc2))
      throw GeoCal::Exception("Unsupported ImageGroundConnection type");
    igc_list.push_back(Igc);
    if((int) igc_list.size() == 1)
      add_igc_object();
  }
  void nearest_attitude_time_point(const boost::shared_ptr<GeoCal::Time>& T,
				   boost::shared_ptr<GeoCal::Time>& Tbefore,
				   boost::shared_ptr<GeoCal::Time>& Tafter) const;
  virtual void print(std::ostream& Os) const;
private:
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  void add_igc_object();
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressIgcCollection);
  
#endif
