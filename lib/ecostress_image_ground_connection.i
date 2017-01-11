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
   int Band= REF_BAND);
  virtual boost::shared_ptr<GroundCoordinate> 
  ground_coordinate_dem(const ImageCoordinate& Ic,
			const Dem& D) const;
  virtual ImageCoordinate image_coordinate(const GroundCoordinate& Gc) 
    const;
  %python_attribute_with_set(band, int)
  %python_attribute_with_set(orbit, boost::shared_ptr<GeoCal::Orbit>);
  %python_attribute_with_set(time_table,boost::shared_ptr<GeoCal::TimeTable>);
  %python_attribute_with_set(camera,boost::shared_ptr<GeoCal::Camera>);
  %python_attribute_with_set(scan_mirror,
			     boost::shared_ptr<EcostressScanMirror>);
  %pickle_serialization();
};
}

