#ifndef ECOSTRESS_IGC_COLLECTION_H
#define ECOSTRESS_IGC_COLLECTION_H
#include "ecostress_image_ground_connection.h"
#include "igc_array.h"

namespace Ecostress {
/****************************************************************//**
  This is a collection of EcostressImageGroundConnection. This is just
  a IgcArray, with a few convenience functions put in. We may remove 
  this as a separate class, for but now we'll have this in place.
*******************************************************************/

class EcostressIgcCollection : public virtual GeoCal::IgcArray {
public:
  EcostressIgcCollection()
  { assume_igc_independent_ = false; }
  virtual ~EcostressIgcCollection() {}
  virtual void add_igc
  (const boost::shared_ptr<EcostressImageGroundConnection>& Igc)
  { igc_list.push_back(Igc);
    if((int) igc_list.size() == 1)
      add_object(Igc->orbit());
  }
  virtual blitz::Array<double, 2> 
  image_coordinate_jac_parm(int Image_index, const GeoCal::CartesianFixed& Gc) 
    const
  {
    // Hopefully this is temporary. Having trouble sorting out the
    // calculation of the jacobian, so in the short time just do
    // finite difference calculation.
    blitz::Array<double, 1> pstep(parameter_subset().rows());
    pstep(blitz::Range::all()) = 1.0;
    return image_coordinate_jac_parm_fd(Image_index, Gc, pstep);
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
