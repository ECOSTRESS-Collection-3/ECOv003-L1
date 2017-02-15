#ifndef SIMULATED_RADIANCE_H
#define SIMULATED_RADIANCE_H
#include "ground_coordinate_array.h"
#include "geocal/raster_image.h"

namespace Ecostress {
/****************************************************************//**
  This is used to produce simulated radiance data. This is based on
  an underlying Map_projected_image (e.g., ASTER data), and we
  simulate what ecostress would see when viewing this data. The
  simulated data is like L1A_PIX data, except that it is still in
  whatever units the Map_projected_image is. A separate step is needed
  to convert this into DNs to make a proper L1A_PIX file.
*******************************************************************/

class SimulatedRadiance : public GeoCal::Printable<SimulatedRadiance> {
public:
  SimulatedRadiance(const boost::shared_ptr<GroundCoordinateArray>& Gca)
    : gca_(Gca)
  {}
  virtual ~SimulatedRadiance() {}

//-------------------------------------------------------------------------
/// Return underlying GroundCoordinateArray.
//-------------------------------------------------------------------------

  const boost::shared_ptr<GroundCoordinateArray>& ground_coordinate_array()
    const {return gca_;}
  virtual void print(std::ostream& Os) const;
private:
  boost::shared_ptr<GroundCoordinateArray> gca_;
  void init();
  SimulatedRadiance() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  template<class Archive>
  void save(Archive & ar, const unsigned int version) const;
  template<class Archive>
  void load(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::SimulatedRadiance);
#endif

