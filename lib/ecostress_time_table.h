#ifndef ECOSTRESS_TIME_TABLE_H
#define ECOSTRESS_TIME_TABLE_H
#include "geocal/time_table.h"

namespace Ecostress {
/****************************************************************//**
  This is the ecostress time table.

  The table is different before and after we do the 2 line averaging
  in L1B_CAL, we indicate this by "averaging_done" set to true, which
  means each scan is treated as 128 lines rather than 256.

  Note that only the image coordinates changes from 128/256 per scan
  index. The FrameCoordinate are in terms of the actual Ecostress
  camera, so there is always 256 frame coordinate lines in a scan.
*******************************************************************/
class EcostressTimeTable: public GeoCal::TimeTable {
public:
  EcostressTimeTable(GeoCal::Time Tstart, bool Averaging_done = true,
		     int Num_scan = 44, double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875);
  EcostressTimeTable(const std::vector<GeoCal::Time> Tstart_scan,
		     bool Averaging_done = true, double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875);
  EcostressTimeTable(const std::string& Fname, double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875,
		     double Toffset = 0);
  EcostressTimeTable(const std::string& Fname, bool Averaging_done,
		     double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875, double Toffset=0);
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
  { return (int) tstart_scan_.size() * number_line_scan() - 1; }
  virtual GeoCal::Time min_time() const { return tstart_scan_[0]; }
  virtual GeoCal::Time max_time() const
  { return *tstart_scan_.rbegin() + nominal_scan_time(); }
  virtual void print(std::ostream& Os) const;
  int number_line_scan() const { return (averaging_done_ ? 128 : 256); }

//-------------------------------------------------------------------------
/// Number of scans we have.
//-------------------------------------------------------------------------

  int number_scan() const {return (int) tstart_scan_.size(); }

//-------------------------------------------------------------------------
/// Number of times that we filled in the scan time because it was missing
//-------------------------------------------------------------------------

  int number_filled_time() const {return number_filled_time_; }
  
//-------------------------------------------------------------------------
/// Number of good scans we have (defined as having a valid
/// line_start_time_j2000)
//-------------------------------------------------------------------------

  int number_good_scan() const {return number_scan() - number_filled_time(); }
  
//-------------------------------------------------------------------------
/// Mirror rotation speed, in rotations per minute (nominal, actual
/// speed may be different).
//-------------------------------------------------------------------------

  double mirror_rpm() const { return mirror_rpm_; }

//-------------------------------------------------------------------------
/// Nominal spacing in seconds between scans. The actual time may be
/// different, but this is the best approximation.
//-------------------------------------------------------------------------

  double nominal_scan_time() const
  {
    // The "/ 2" is because we get data on both sides of the mirror,
    // so a scan takes 1/2 the time it takes for a full rotation.
    return (60.0 / mirror_rpm_) / 2;
  }

//-------------------------------------------------------------------------
/// Time in seconds between frames/samples.
//-------------------------------------------------------------------------

  double frame_time() const {return frame_time_;}

//-------------------------------------------------------------------------
/// Test of a particular line is close to the edge of scan line. This
/// is used by EcostressInterpolate to avoid training of data that crosses
/// a scan region, since this data has discontinuities. 
//-------------------------------------------------------------------------
 
  bool close_to_scan_edge(int Line, int Width=3) const
  {
    int i = Line % number_line_scan();
    return i < Width || i >= (number_line_scan() - Width);
  }
  
//-------------------------------------------------------------------------
/// Image lines that go with a scan. Note this is the normal C
/// convention of including the start but not the end, so
/// Lstart <= L < Lend for L in scan Scan_index
//-------------------------------------------------------------------------
  
  void scan_index_to_line(int Scan_index, int& Lstart, int& Lend) const
  { range_check(Scan_index, 0, number_scan());
    Lstart = number_line_scan() * Scan_index;
    Lend = number_line_scan() * (Scan_index+1);
  }

  const std::vector<GeoCal::Time>& tstart_scan() const { return tstart_scan_;}
  
//-------------------------------------------------------------------------
/// Convert line to scan index
//-------------------------------------------------------------------------
  int line_to_scan_index(double Line) const
  { return (int) floor(Line / number_line_scan()); }
protected:
  EcostressTimeTable() : mirror_rpm_(25.4), frame_time_(0.0000321875),
			 number_filled_time_(0) { }
  bool averaging_done_;
  std::vector<GeoCal::Time> tstart_scan_;
  double mirror_rpm_, frame_time_;
  int number_filled_time_;
private:
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  void read_file(const std::string& Fname, double Toffset);
};

class EcostressTimeTableSubset: public EcostressTimeTable {
public:
  EcostressTimeTableSubset(const EcostressTimeTable& Tt, int Start_sample, int Number_sample);
  virtual ~EcostressTimeTableSubset() {}
  int start_sample() const { return start_sample_; }
  virtual void print(std::ostream& Os) const;

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
private:
  int start_sample_, num_sample_;
  EcostressTimeTableSubset() { }
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressTimeTable);
BOOST_CLASS_VERSION(Ecostress::EcostressTimeTable, 2);
BOOST_CLASS_EXPORT_KEY(Ecostress::EcostressTimeTableSubset);
#endif

