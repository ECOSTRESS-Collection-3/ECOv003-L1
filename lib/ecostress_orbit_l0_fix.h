#ifndef ECOSTRESS_ORBIT_L0_H
#define ECOSTRESS_ORBIT_L0_H
#include "orbit_array.h"
#include "hdf_file.h"

namespace Ecostress {
/****************************************************************//**
  This is a variation of the EcostressOrbit where we correct for the
  wrong L0 time tags. This class should go away once L0 software has
  been fixed and we've regenerated all the data.

  It would be nice just to have a flag in EcostressOrbit to turn the
  fix on or off, but unfortunately the layout of the code makes this
  pretty much impossible without making changed to geocal. Not worth
  it for a one off fix that will go away in the future.
*******************************************************************/

class EcostressOrbitL0Fix : public GeoCal::OrbitArray<GeoCal::Eci,
					       GeoCal::TimeJ2000Creator> {
public:
//-------------------------------------------------------------------------
/// Constructor, read the give file and allow the given amount of
/// extrapolation pad. Treat gaps in the data > Large_gap as a large
/// gap. 
//-------------------------------------------------------------------------
  EcostressOrbitL0Fix(const std::string& Fname, double Extrapolation_pad = 5.0,
		      double Large_gap = 10.0, bool Apply_fix = true)
    : fname(Fname),
      apply_fix_(Apply_fix),
      large_gap_(Large_gap),
      pad_(Extrapolation_pad)
  {
    OrbitArray<GeoCal::Eci, GeoCal::TimeJ2000Creator>::att_from_sc_to_ref_frame = true;
    init();
  }

//-------------------------------------------------------------------------
/// Constructor, read the give file and allow the given amount of
/// extrapolation pad. Treat gaps in the data > Large_gap as a large
/// gap. Also has an offset in position like OrbitScCoorOffset.
//-------------------------------------------------------------------------

  EcostressOrbitL0Fix(const std::string& Fname,
		      const blitz::Array<double, 1>& Pos_off,
		      double Extrapolation_pad = 5.0,
		      double Large_gap = 10.0,
		      bool Apply_fix = true)
    : fname(Fname),
      apply_fix_(Apply_fix),
      large_gap_(Large_gap),
      pad_(Extrapolation_pad),
      pos_off_(Pos_off.copy())
  {
    if(Pos_off.rows() != 3)
      throw GeoCal::Exception("Pos_off needs to be size 3");
    OrbitArray<GeoCal::Eci, GeoCal::TimeJ2000Creator>::att_from_sc_to_ref_frame = true;
    init();
  }
  virtual ~EcostressOrbitL0Fix() {}

  bool spacecraft_x_mostly_in_velocity_direction(GeoCal::Time T) const;

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

//-----------------------------------------------------------------------
/// Return the file name
//-----------------------------------------------------------------------

  const std::string& file_name() const {return fname;}

//-----------------------------------------------------------------------
/// Return true if we are applying the L0 time tag fix to wrong L0
/// time tags.
//-----------------------------------------------------------------------

  bool apply_fix() const {return apply_fix_;}
  
  virtual void print(std::ostream& Os) const;
protected:
  virtual boost::shared_ptr<GeoCal::QuaternionOrbitData>
  orbit_data_create(GeoCal::Time T) const;
  virtual void interpolate_or_extrapolate_data
  (GeoCal::Time T, boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q1,
   boost::shared_ptr<GeoCal::QuaternionOrbitData>& Q2) const;
private:
  void init();
  std::string fname;
  bool apply_fix_;
  double large_gap_, pad_;
  blitz::Array<double, 1> pos_off_;
  EcostressOrbitL0Fix() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  template<class Archive>
  void save(Archive& Ar, const unsigned int version) const;
  template<class Archive>
  void load(Archive& Ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressOrbitL0Fix);
#endif

