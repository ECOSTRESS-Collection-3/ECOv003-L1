#include "ecostress_time_table.h"
#include "ecostress_serialize_support.h"
#include "geocal/hdf_file.h"
#include <algorithm>
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressTimeTable::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(TimeTable)
    & GEOCAL_NVP_(averaging_done)
    & GEOCAL_NVP_(tstart_scan);
  // Older version didn't have mirror_rpm_ or frame_time_, but
  // used hardcoded values. We set the hardcoded values in the default
  // constructor.
  if(version > 0)
    ar & GEOCAL_NVP_(mirror_rpm) & GEOCAL_NVP_(frame_time);
  // Older version didn't track number_filled_time_. We initialize
  // this to zero in the default constructor
  if(version > 1)
    ar & GEOCAL_NVP_(number_filled_time);
}

ECOSTRESS_IMPLEMENT(EcostressTimeTable);

//-------------------------------------------------------------------------
/// Create a time table by reading the input file. The file should be
/// a L1A_PIX or a L1B_RAD file
//-------------------------------------------------------------------------

EcostressTimeTable::EcostressTimeTable(const std::string& Fname,
				       double Mirror_rpm, double Frame_time,
				       double Toffset)
  : mirror_rpm_(Mirror_rpm),
    frame_time_(Frame_time),
    number_filled_time_(0)
{
  read_file(Fname, Toffset);
}

//-------------------------------------------------------------------------
/// Create a time table by reading the input file. The file should be
/// a L1A_PIX or a L1B_RAD file.
///
/// This variation lets you set the Averaging_done
/// explicitly. Normally we  just set Averaging_done for L1B_RAD and
/// have it false for L1A_PIX. But for testing purposes it can be
/// useful to read one dataset and then pretend it for a different
/// averaging mode.
//-------------------------------------------------------------------------

EcostressTimeTable::EcostressTimeTable
(const std::string& Fname, bool Averaging_done,
 double Mirror_rpm, double Frame_time, double Toffset)
  : mirror_rpm_(Mirror_rpm),
    frame_time_(Frame_time),
    number_filled_time_(0)
{
  read_file(Fname, Toffset);
  averaging_done_ = Averaging_done;
}

//-------------------------------------------------------------------------
/// Read a file to populate the data.
//-------------------------------------------------------------------------

void EcostressTimeTable::read_file(const std::string& Fname, double Toffset)
{
  GeoCal::HdfFile f(Fname);
  averaging_done_ = f.has_object("/L1B_RADMetadata");
  blitz::Array<double, 1> t = f.read_field<double, 1>("/Time/line_start_time_j2000");
  t -= Toffset;
  for(int i = 0; i < t.rows(); i += number_line_scan()) {
    // Check for fill data. We need a "reasonable" value even if the
    // time is missing, so we just use the nominal_scan_time().
    if(t(i) == 0.0) {
      if(i == 0)
	throw Exception("Don't currently handle fill data at the first line in the image");
      tstart_scan_.push_back(tstart_scan_.back() + nominal_scan_time());
      ++number_filled_time_;
    } else 
      tstart_scan_.push_back(GeoCal::Time::time_j2000(t(i)));
  }
}

//-------------------------------------------------------------------------
/// Create a time table with the given number of scans, with the time
/// spaced exactly the nominal_scan_time().
//-------------------------------------------------------------------------

EcostressTimeTable::EcostressTimeTable
(GeoCal::Time Tstart, bool Averaging_done, int Num_scan,
 double Mirror_rpm, double Frame_time)
  : averaging_done_(Averaging_done),
    mirror_rpm_(Mirror_rpm),
    frame_time_(Frame_time),
    number_filled_time_(0)
{
  for(int i = 0; i < Num_scan; ++i)
    tstart_scan_.push_back(Tstart + i * nominal_scan_time());
}

//-------------------------------------------------------------------------
/// Create a time table with the given start time of each scan.
//-------------------------------------------------------------------------

EcostressTimeTable::EcostressTimeTable
(const std::vector<GeoCal::Time> Tstart_scan, bool Averaging_done,
 double Mirror_rpm, double Frame_time)
 
: averaging_done_(Averaging_done),
  tstart_scan_(Tstart_scan),
  mirror_rpm_(Mirror_rpm),
  frame_time_(Frame_time),
  number_filled_time_(0)
{
  // Nothing more to do
}

// See base class for description
GeoCal::ImageCoordinate EcostressTimeTable::image_coordinate
(GeoCal::Time T, const GeoCal::FrameCoordinate& F) const
{
  range_check_inclusive(T, min_time(), max_time());
  int tindex = std::lower_bound(tstart_scan_.begin(), tstart_scan_.end(), T) -
    tstart_scan_.begin();
  if(tindex == (int) tstart_scan_.size() || tstart_scan_[tindex] > T)
    --tindex;
  ImageCoordinate res;
  if(averaging_done()) 
    res.line = F.line / 2.0 + tindex * number_line_scan();
  else
    res.line = F.line + tindex * number_line_scan();
  res.sample = (T - tstart_scan_[tindex]) / frame_time() + F.sample;
  return res;
}

// See base class for description
GeoCal::ImageCoordinateWithDerivative 
EcostressTimeTable::image_coordinate_with_derivative
  (const GeoCal::TimeWithDerivative& T, 
   const GeoCal::FrameCoordinateWithDerivative& F) const
{
  range_check_inclusive(T.value(), min_time(), max_time());
  int tindex = std::lower_bound(tstart_scan_.begin(), tstart_scan_.end(),
				T.value()) - tstart_scan_.begin();
  if(tindex == (int) tstart_scan_.size() || tstart_scan_[tindex] > T.value())
    --tindex;
  ImageCoordinateWithDerivative res;
  if(averaging_done()) 
    res.line = F.line / 2.0 + tindex * number_line_scan();
  else
    res.line = F.line + tindex * number_line_scan();
  res.sample = (T - tstart_scan_[tindex]) / frame_time() + F.sample;
  return res;
}

// See base class for description
void EcostressTimeTable::time
(const GeoCal::ImageCoordinate& Ic,
 GeoCal::Time& T, GeoCal::FrameCoordinate& F) const
{
  range_check(Ic.line, (double) min_line(), (double) max_line() + 1.0);
  int tindex = (int) floor(Ic.line / number_line_scan());
  F.line = Ic.line - (tindex * number_line_scan());
  if(averaging_done())
    F.line *= 2.0;
  T = tstart_scan_[tindex] + frame_time() * Ic.sample;
  F.sample = 0;
}

// See base class for description
void EcostressTimeTable::time_with_derivative
  (const GeoCal::ImageCoordinateWithDerivative& Ic, 
   GeoCal::TimeWithDerivative& T, 
   GeoCal::FrameCoordinateWithDerivative& F) const
{
  range_check(Ic.line.value(), (double) min_line(), (double) max_line() + 1.0);
  int tindex = (int) floor(Ic.line.value() / number_line_scan());
  F.line = Ic.line - (tindex * number_line_scan());
  if(averaging_done())
    F.line *= 2.0;
  T = GeoCal::TimeWithDerivative(tstart_scan_[tindex]) +
    frame_time() * Ic.sample;
  F.sample = 0;
}

void EcostressTimeTable::print(std::ostream& Os) const
{
  Os << "EcostressTimeTable:\n"
     << "  Start time:           " << min_time() << "\n"
     << "  Number scan:          " << tstart_scan_.size() << "\n"
     << "  Averaging done:       " << (averaging_done_ ? "True\n" : "False\n")
     << "  Mirror RPM (nominal): " << mirror_rpm_ << "\n"
     << "  Frame time:           " << frame_time_ << " s\n";
}




  
