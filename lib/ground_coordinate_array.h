#ifndef GROUND_COORDINATE_ARRAY_H
#define GROUND_COORDINATE_ARRAY_H
#include "ecostress_image_ground_connection.h"

namespace Ecostress {
/****************************************************************//**
  While we can just use the normal EcostressImageGroundConnection 
  ground_coordinate function to calculate the ground coordinate for a 
  range of image coordinates, it can take a while to do this.

  We can significantly speed this up if we have a good initial guess
  as the starting length of each ray when finding the intersection of
  the surface.

  We do this by noting that as be scan across the full set of samples
  the rays are near parallel from one scan position to the next. We
  take advantage of this by first doing a full calculation for the
  nadir most scan position, and then approximate each scan position
  outside of this as starting at the distance for the previous can
  position. We improve the guess a bit by not just using one ray, but
  also looking and the line just above and below a given line.

  Note that this is very similar to the IgcRayCaster class found in
  GeoCal. However that is designed for a pushbroom camera, while we
  have a push whisk broom. So we use different logic for coming up
  with the initial guess as the ray length, but it is the same
  idea. We also don't actually need to do this with subpixels for this
  particular application, so we simplify the logic a little bit by
  only worrying about the middle of each image pixel.
*******************************************************************/

class GroundCoordinateArray : public GeoCal::Printable<GroundCoordinateArray> {
public:
  GroundCoordinateArray(const boost::shared_ptr<EcostressImageGroundConnection>& Igc)
    : igc_(Igc) { init(); }
  virtual ~GroundCoordinateArray() {}
  virtual void print(std::ostream& Os) const;
  const boost::shared_ptr<EcostressImageGroundConnection>&  igc() const
  { return igc_;}
private:
  boost::shared_ptr<EcostressImageGroundConnection> igc_;
  void init();
  GroundCoordinateArray() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  template<class Archive>
  void save(Archive & ar, const unsigned int version) const;
  template<class Archive>
  void load(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::GroundCoordinateArray);
#endif

  
  
