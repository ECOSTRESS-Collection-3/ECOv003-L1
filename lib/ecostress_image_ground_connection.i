// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_image_ground_connection.h"
%}
%geocal_base_import(image_ground_connection)
%import "orbit.i"
%import "camera.i"
%import "time_table.i"
%import "ecostress_scan_mirror.i"
%import "dem.i"
%import "raster_image.i"
%ecostress_shared_ptr(Ecostress::EcostressImageGroundConnection);
namespace Ecostress {
class EcostressImageGroundConnection : public GeoCal::ImageGroundConnection {
public:
  enum {REF_BAND = 4 }; 	// Not sure about this, we'll need to
				// check on this
  EcostressImageGroundConnection
  (const boost::shared_ptr<GeoCal::Orbit>& Orb,
   const boost::shared_ptr<GeoCal::TimeTable>& Tt,
   const boost::shared_ptr<GeoCal::Camera>& Cam,
   const boost::shared_ptr<EcostressScanMirror>& Scan_mirror,
   const boost::shared_ptr<GeoCal::Dem>& D,
   const boost::shared_ptr<GeoCal::RasterImage>& Img,
   const std::string& Title = "",
   double Resolution=30, int Band= REF_BAND, double Max_height=9000);
  virtual boost::shared_ptr<GeoCal::GroundCoordinate> 
  ground_coordinate_dem(const GeoCal::ImageCoordinate& Ic,
			const GeoCal::Dem& D) const;
  virtual GeoCal::ImageCoordinate image_coordinate
  (const GeoCal::GroundCoordinate& Gc) const;
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::Time& T, double Ic_line, double Ic_sample) const;
  boost::shared_ptr<GeoCal::QuaternionOrbitData> orbit_data
  (const GeoCal::TimeWithDerivative& T, double Ic_line,
   const GeoCal::AutoDerivative<double>& Ic_sample) const;
  void image_coordinate_scan_index
  (const GeoCal::GroundCoordinate& Gc,
   int Scan_index, GeoCal::ImageCoordinate& OUTPUT, bool& OUTPUT,
   int Band=-1) const;
  %python_attribute(number_line_scan, int);
  %python_attribute_with_set(band, int);
  %python_attribute_with_set(resolution, double);
  %python_attribute_with_set(max_height, double);
  %python_attribute_with_set(orbit, boost::shared_ptr<GeoCal::Orbit>);
  %python_attribute_with_set(time_table,boost::shared_ptr<GeoCal::TimeTable>);
  %python_attribute_with_set(camera,boost::shared_ptr<GeoCal::Camera>);
  %python_attribute_with_set(scan_mirror,
			     boost::shared_ptr<EcostressScanMirror>);
  %pickle_serialization();
};
}

// List of things "import *" will include
%python_export("EcostressImageGroundConnection")

