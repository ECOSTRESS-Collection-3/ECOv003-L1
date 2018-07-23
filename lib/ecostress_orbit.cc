#include "ecostress_orbit.h"
#include "ecostress_serialize_support.h"
#include <boost/make_shared.hpp>
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressOrbit::save(Archive& Ar, const unsigned int version) const
{
  // Nothing more to do
}

template<class Archive>
void EcostressOrbit::load(Archive& Ar, const unsigned int version)
{
  init();
}

template<class Archive>
void EcostressOrbit::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(HdfOrbit_Eci_TimeJ2000)
    & GEOCAL_NVP_(large_gap)
    & GEOCAL_NVP_(pad)
    & GEOCAL_NVP_(pos_off);
  boost::serialization::split_member(ar, *this, version);
}

ECOSTRESS_IMPLEMENT(EcostressOrbit);

/// See base class for description
void EcostressOrbit::print(std::ostream& Os) const
{
  Os << "EcostressOrbit\n"
     << "  File name:        " << file_name() << "\n"
     << "  Min time:         " << min_time() << "\n"
     << "  Max time:         " << max_time() << "\n"
     << "  Large gap:        " << large_gap() << " s\n"
     << "  Extrapolation pad: " << extrapolation_pad() << " s\n";
  if(pos_off_.rows() < 3)
    Os << "  Position offset:   None";
  else
    Os << "  Position offset:   ("
       << pos_off_(0) << ", " 
       << pos_off_(1) << ", " 
       << pos_off_(2) << ")\n";
}


/// See base class for description
void EcostressOrbit::interpolate_or_extrapolate_data
(GeoCal::Time T, boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q1,
 boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q2) const
{
  range_check_inclusive(T, min_time(), max_time());
  time_map::iterator i = orbit_data_map.lower_bound(T);
  // Handle extrapolation past beginning of data
  if(i == orbit_data_map.end())
    i = orbit_data_map.lower_bound(orbit_data_map.rbegin()->first);
  check_lazy_evaluation(i);
  // Special handling if we are looking at the very first point
  if(i == orbit_data_map.begin() && T - i->first <= 0.0) {
    ++i;
    check_lazy_evaluation(i);
  }
  Q2 = i->second;
  --i;
  check_lazy_evaluation(i);
  Q1 = i->second;
  // Handling for large gaps
  if(Q2->time() - Q1->time() > large_gap_) {
    if(T - Q1->time() <= pad_ && i != orbit_data_map.begin()) {
      Q2 = Q1;
      --i;
      check_lazy_evaluation(i);
      Q1 = i->second;
      return;
    }
    ++i;
    if(Q2->time() - T <= pad_ && i != orbit_data_map.end()) {
      Q1 = Q2;
      ++i;
      check_lazy_evaluation(i);
      Q2 = i->second;
      return;
    }
    GeoCal::Exception e;
    e << "Request time is in the middle of a large gap:\n"
      << "  T:         " << T << "\n"
      << "  Gap start: " << Q1->time() << "\n"
      << "  Gap end:   " << Q2->time() << "\n";
    throw e;
  }
}

/// See base class for description

boost::shared_ptr<GeoCal::QuaternionOrbitData>
EcostressOrbit::orbit_data_create(GeoCal::Time T) const
{
  boost::shared_ptr<QuaternionOrbitData> od =
  GeoCal::HdfOrbit<GeoCal::Eci, GeoCal::TimeJ2000Creator>::orbit_data_create(T);
  if(pos_off_.rows() < 3)
    return od;
  ScLookVector slv(pos_off_(0), pos_off_(1), pos_off_(2));
  boost::array<double, 3> pos_off;
  if(od->from_cf()) {
    CartesianFixedLookVector lv = od->cf_look_vector(slv);
    pos_off = lv.look_vector;
  } else {
    CartesianInertialLookVector lv = od->ci_look_vector(slv);
    pos_off = lv.look_vector;
  }
  return boost::make_shared<QuaternionOrbitData>(*od, pos_off,
			 boost::math::quaternion<double>(1,0,0,0));
}

//-------------------------------------------------------------------------
/// Indicate if spacecraft orientation is mostly in the forward
/// direction, or has the 180 degree yaw used sometimes in
/// maneuvers. This controls if the data in l1a_pix looks "upside
/// down", if this is true than it is upside down and l1b_rad should
/// flip this.
//-------------------------------------------------------------------------

bool EcostressOrbit::spacecraft_x_mostly_in_velocity_direction
(GeoCal::Time T) const
{
  boost::shared_ptr<OrbitData> od = orbit_data(T);
  CartesianInertialLookVector clv(od->velocity_ci());
  ScLookVector slv = od->sc_look_vector(clv);
  return (slv.look_vector[0] > 0);
}
