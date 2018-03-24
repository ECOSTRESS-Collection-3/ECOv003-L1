#ifndef ECOSTRESS_IGC_COLLECTION_H
#define ECOSTRESS_IGC_COLLECTION_H
#include "ecostress_image_ground_connection.h"
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
  virtual void add_igc
  (const boost::shared_ptr<EcostressImageGroundConnection>& Igc)
  { igc_list.push_back(Igc);
    if((int) igc_list.size() == 1) {
      add_object(Igc->camera());
      add_object(Igc->orbit());
      add_object(Igc->time_table());
    }
  }
  virtual void print(std::ostream& Os) const;
private:
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressIgcCollection);
  
#endif
