#ifndef ECOSTRESS_TIME_TABLE_H
#define ECOSTRESS_TIME_TABLE_H
#include "geocal/time_table.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress time table.

  Right now this is pretty much a place holder. We assume constant
  time spacing between pixels.

  The table is different before and after we do the 2 line averaging
  in L1B_CAL, we indicate this by "averaging_done" set to true, which
  means each scan is treated as 128 lines rather than 256.
*******************************************************************/
class EcostressTimeTable: public GeoCal::TimeTable {
public:
  EcostressTimeTable(GeoCal::Time Tstart, bool Averaging_done = true,
		     int Num_scan = 44);
  EcostressTimeTable(const std::vector<GeoCal::Time> Tstart_scan,
		     bool Averaging_done = true);
  virtual ~EcostressTimeTable() {}

//-------------------------------------------------------------------------
/// If true, then we have already done the 2 line averaging. Each scan
/// is 256 lines if this is false, 128 if it is true.
//-------------------------------------------------------------------------

  bool averaging_done() const {return averaging_done_;}

  virtual GeoCal::ImageCoordinate image_coordinate(GeoCal::Time T,
					   const GeoCal::FrameCoordinate& F)
    const;
  virtual GeoCal::ImageCoordinateWithDerivative 
  image_coordinate_with_derivative
  (const GeoCal::TimeWithDerivative& T, 
   const GeoCal::FrameCoordinateWithDerivative& F) const;
  virtual void time(const GeoCal::ImageCoordinate& Ic,
		    GeoCal::Time& T, GeoCal::FrameCoordinate& F) const;
  virtual void time_with_derivative
  (const GeoCal::ImageCoordinateWithDerivative& Ic, 
   GeoCal::TimeWithDerivative& T, 
   GeoCal::FrameCoordinateWithDerivative& F) const;
  virtual int min_line() const {return 0;}
  virtual int max_line() const
  { return (int) tstart_scan_.size() * number_line_scan(); }
  virtual GeoCal::Time min_time() const { return tstart_scan_[0]; }
  virtual GeoCal::Time max_time() const
  { return *tstart_scan_.rbegin() + nominal_scan_spacing; }
  virtual void print(std::ostream& Os) const;
  const static double nominal_scan_spacing;
  const static double frame_time;
  int number_line_scan() const { return (averaging_done_ ? 128 : 256); }
private:
  bool averaging_done_;
  std::vector<GeoCal::Time> tstart_scan_;
  EcostressTimeTable() { }
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressTimeTable);
#endif

