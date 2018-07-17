#ifndef ECOSTRESS_ORBIT_H
#define ECOSTRESS_ORBIT_H
#include "geocal/hdf_orbit.h"

namespace Ecostress {
/****************************************************************//**
  This is the Ecostress orbit (not including any fixes or
  modifications). This is used to read a L1A_ATT or L1B_ATT file.

  This is mostly just a plain vanilla HdfOrbit, however we have two
  modifications:

  1. The BAD data is collected at different times than the image data.
     In general, the time for image data and the time for the orbit
     aren't exactly the same. They are close, within a second or
     two. But we want to allow a limited extrapolation at the start
     and end of the orbit (a HdfOrbit treats this as an error)
  2. The BAD data is only collected at the same time as the
     imagery. We can have large gaps in the ephemeris and attitude
     when we collect data for a scene, wait for a bit, and then
     collect another scene. A HdfOrbit interpolates between data, but
     this doesn't make sense for large gaps. Instead, we will use the
     data near the time requested and extrapolate. Times too far into
     a large gap will be treated as errors. So basically we divide the
     full orbit into a number of smaller orbits covering the scenes,
     and allow extrapolation of the data.
*******************************************************************/

class EcostressOrbit : public GeoCal::HdfOrbit<GeoCal::Eci,
					       GeoCal::TimeJ2000Creator> {
public:
//-------------------------------------------------------------------------
/// Constructor, read the give file and allow the given amount of
/// extrapolation pad. Treat gaps in the data > Large_gap as a large
/// gap. 
//-------------------------------------------------------------------------
  EcostressOrbit(const std::string& Fname, double Extrapolation_pad = 5.0,
		 double Large_gap = 10.0)
    : GeoCal::HdfOrbit<GeoCal::Eci, GeoCal::TimeJ2000Creator>
    (Fname, "", "Ephemeris/time_j2000", "Ephemeris/eci_position",
     "Ephemeris/eci_velocity", "Attitude/time_j2000", "Attitude/quaternion"),
    large_gap_(Large_gap),
    pad_(Extrapolation_pad)
  {
    // Add padding to min and max time.
    min_tm -= Extrapolation_pad;
    max_tm += Extrapolation_pad;
  }
  virtual ~EcostressOrbit() {}

//-------------------------------------------------------------------------
/// Allow extrapolation up this amount. Given in seconds.
//-------------------------------------------------------------------------

  double extrapolation_pad() const {return pad_;}
  void extrapolation_pad(double v) { pad_ = v;}

//-------------------------------------------------------------------------
/// Threshold for considering a gap in the data "large". This is in
/// seconds. Data in a large gap is not interpolated.
//-------------------------------------------------------------------------

  double large_gap() const {return large_gap_;}
  void large_gap(double v) { large_gap_ = v;}

  virtual void print(std::ostream& Os) const;
protected:
  virtual void interpolate_or_extrapolate_data
  (GeoCal::Time T, boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q1,
   boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q2) const;
private:
  double large_gap_, pad_;
  EcostressOrbit() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressOrbit);
#endif

