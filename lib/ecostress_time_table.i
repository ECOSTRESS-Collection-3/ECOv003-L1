// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_time_table.h"
%}

%geocal_base_import(time_table)

%ecostress_shared_ptr(Ecostress::EcostressTimeTable);
%ecostress_shared_ptr(Ecostress::EcostressTimeTableSubset);
namespace Ecostress {
class EcostressTimeTable : public GeoCal::TimeTable {
public:
  EcostressTimeTable(GeoCal::Time Tstart, bool Averaging_done = True,
		     int Num_scan = 44, double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875);
  EcostressTimeTable(const std::vector<GeoCal::Time> Tstart_scan,
		     bool Averaging_done = True, double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875);
  EcostressTimeTable(const std::string& Fname, double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875,
		     double Toffset = 0);
  EcostressTimeTable(const std::string& Fname, bool Averaging_done,
		     double Mirror_rpm = 25.4,
		     double Frame_time = 0.0000321875,
		     double Toffset = 0);
  virtual GeoCal::ImageCoordinate image_coordinate
    (GeoCal::Time T, const GeoCal::FrameCoordinate& F) const;
  void scan_index_to_line(int Scan_index, int& OUTPUT, int& OUTPUT) const;
  int line_to_scan_index(double Line) const;
  bool close_to_scan_edge(int Line, int Width=3) const;
  %python_attribute(averaging_done, bool);
  %python_attribute(number_line_scan, int);
  %python_attribute(number_good_scan, int);
  %python_attribute(number_scan, int);
  %python_attribute(mirror_rpm, double);
  %python_attribute(nominal_scan_time, double);
  %python_attribute(frame_time, double);
  %python_attribute(tstart_scan, std::vector<GeoCal::Time>);
  %pickle_serialization();
};

class EcostressTimeTableSubset : public EcostressTimeTable {
public:
  EcostressTimeTableSubset(const EcostressTimeTable& Tt, int Start_sample, int Number_sample);
  %python_attribute(start_sample, int);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressTimeTable", "EcostressTimeTableSubset")

