#include "ecostress_time_table.h"
#include "ecostress_serialize_support.h"
#include <algorithm>
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void EcostressTimeTable::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(TimeTable)
    & GEOCAL_NVP_(averaging_done)
    & GEOCAL_NVP_(tstart_scan);
}

ECOSTRESS_IMPLEMENT(EcostressTimeTable);

// These numbers come for the the ECOSTRESS_SDS_Data_Bible.xls in
// the Ecostress-sds git repository.
const double EcostressTimeTable::nominal_scan_spacing = 1.181;
const double EcostressTimeTable::frame_time = 32.2e-6;

//-------------------------------------------------------------------------
/// Create a time table with the given number of scans, with the time
/// spaced exactly the nominal_scan_spacing.
//-------------------------------------------------------------------------

EcostressTimeTable::EcostressTimeTable
(GeoCal::Time Tstart, bool Averaging_done, int Num_scan)
  : averaging_done_(Averaging_done)
{
  for(int i = 0; i < Num_scan; ++i)
    tstart_scan_.push_back(Tstart + i * nominal_scan_spacing);
}

//-------------------------------------------------------------------------
/// Create a time table with the given start time of each scan.
//-------------------------------------------------------------------------

EcostressTimeTable::EcostressTimeTable
(const std::vector<GeoCal::Time> Tstart_scan, bool Averaging_done)
: averaging_done_(Averaging_done),
  tstart_scan_(Tstart_scan)
{
  // Nothing more to do
}

// See base class for description
GeoCal::ImageCoordinate EcostressTimeTable::image_coordinate
(GeoCal::Time T, const GeoCal::FrameCoordinate& F) const
{
  range_check(T, min_time(), max_time());
  int tindex = std::lower_bound(tstart_scan_.begin(), tstart_scan_.end(), T) -
    tstart_scan_.begin();
  if(tindex == (int) tstart_scan_.size() || tstart_scan_[tindex] > T)
    --tindex;
  ImageCoordinate res;
  res.line = F.line + tindex * number_line_scan();
  res.sample = (T - tstart_scan_[tindex]) / frame_time + F.sample;
  return res;
}

// See base class for description
GeoCal::ImageCoordinateWithDerivative 
EcostressTimeTable::image_coordinate_with_derivative
  (const GeoCal::TimeWithDerivative& T, 
   const GeoCal::FrameCoordinateWithDerivative& F) const
{
  range_check(T.value(), min_time(), max_time());
  int tindex = std::lower_bound(tstart_scan_.begin(), tstart_scan_.end(),
				T.value()) - tstart_scan_.begin();
  if(tindex == (int) tstart_scan_.size() || tstart_scan_[tindex] > T.value())
    --tindex;
  ImageCoordinateWithDerivative res;
  res.line = F.line + tindex * number_line_scan();
  res.sample = (T - tstart_scan_[tindex]) / frame_time + F.sample;
  return res;
}

// See base class for description
void EcostressTimeTable::time
(const GeoCal::ImageCoordinate& Ic,
 GeoCal::Time& T, GeoCal::FrameCoordinate& F) const
{
  range_check(Ic.line, 0.0, (double) max_line());
  int tindex = (int) floor(Ic.line / number_line_scan());
  F.line = Ic.line - (tindex * number_line_scan());
  T = tstart_scan_[tindex] + frame_time * Ic.sample;
  F.sample = 0;
}

// See base class for description
void EcostressTimeTable::time_with_derivative
  (const GeoCal::ImageCoordinateWithDerivative& Ic, 
   GeoCal::TimeWithDerivative& T, 
   GeoCal::FrameCoordinateWithDerivative& F) const
{
  range_check(Ic.line.value(), (double) 0, (double) max_line());
  int tindex = (int) floor(Ic.line.value() / number_line_scan());
  F.line = Ic.line - (tindex * number_line_scan());
  T = GeoCal::TimeWithDerivative(tstart_scan_[tindex]) +
    frame_time * Ic.sample;
  F.sample = 0;
}

void EcostressTimeTable::print(std::ostream& Os) const
{
  Os << "EcostressTimeTable:\n"
     << "  Start time:     " << min_time() << "\n"
     << "  Number scan:    " << tstart_scan_.size() << "\n"
     << "  Averaging done: " << (averaging_done_ ? "True\n" : "False\n");
}




  
