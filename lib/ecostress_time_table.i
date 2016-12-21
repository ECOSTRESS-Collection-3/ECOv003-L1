// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_time_table.h"
%}

%geocal_base_import(time_table)

%ecostress_shared_ptr(Ecostress::EcostressTimeTable);
namespace Ecostress {
class EcostressTimeTable : public GeoCal::TimeTable {
public:
  EcostressTimeTable(GeoCal::Time Tstart, bool Averaging_done = True,
		     int Num_scan = 44);
  EcostressTimeTable(const std::vector<GeoCal::Time> Tstart_scan,
		     bool Averaging_done = True);
  virtual GeoCal::ImageCoordinate image_coordinate
    (GeoCal::Time T, const GeoCal::FrameCoordinate& F) const;
  static const double nominal_scan_spacing;
  static const double frame_time;
  %python_attribute(averaging_done, bool);
  %python_attribute(number_line_scan, int);
  %pickle_serialization();
};
}

