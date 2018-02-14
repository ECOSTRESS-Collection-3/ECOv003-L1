#ifndef GROUND_COORDINATE_ARRAY_H
#define GROUND_COORDINATE_ARRAY_H
#include "ecostress_image_ground_connection.h"
#include "ecostress_time_table.h"
#include "geocal/memory_raster_image.h"
#include "geocal/vicar_lite_file.h"

namespace Ecostress {
/****************************************************************//**
  While we can just use the normal EcostressImageGroundConnection 
  ground_coordinate function to calculate the ground coordinate for a 
  range of image coordinates, it can take a while to do this.

  We can significantly speed this up if we have a good initial guess
  as the starting length of each ray when finding the intersection of
  the surface.

  We do this by noting that as be scan across the full set of samples
  the rays are near parallel from one scan position to the next. We
  take advantage of this by first doing a full calculation for the
  nadir most scan position, and then approximate each scan position
  outside of this as starting at the distance for the previous can
  position. We improve the guess a bit by not just using one ray, but
  also looking and the line just above and below a given line.

  Note that this is very similar to the IgcRayCaster class found in
  GeoCal. However that is designed for a pushbroom camera, while we
  have a push whisk broom. So we use different logic for coming up
  with the initial guess as the ray length, but it is the same
  idea. 
*******************************************************************/

class GroundCoordinateArray : public GeoCal::Printable<GroundCoordinateArray>,
			      boost::noncopyable {
// We can't copy this because of the result_cache. We could create a
// copy constructor if this becomes an issue.
public:
//-------------------------------------------------------------------------
/// Constructor.
///
/// Because they are closely related, you can optionally set
/// Include_angle=true and we will include view_zenith, view_azimuth,
/// solar_zenith and solar_azimuth in our calculation.
//-------------------------------------------------------------------------

  GroundCoordinateArray(const boost::shared_ptr<EcostressImageGroundConnection>& Igc,
			bool Include_angle=false, int Nsub_line = 1,
			int Nsub_sample = 1)
    : igc_(Igc), include_angle(Include_angle), nsub_line(Nsub_line),
      nsub_sample(Nsub_sample){ init(); }
  virtual ~GroundCoordinateArray() {}
  virtual void print(std::ostream& Os) const;

//-------------------------------------------------------------------------
/// The ImageGroundConnection we are working with.
//-------------------------------------------------------------------------
  
  const boost::shared_ptr<EcostressImageGroundConnection>&  igc() const
  { return igc_;}
  blitz::Array<double,5> ground_coor_arr() const;
  blitz::Array<double,5>
  ground_coor_scan_arr(int Start_line, int Number_line=-1) const;
  static blitz::Array<double, 2>
  interpolate(const GeoCal::RasterImage& Data,
	      const blitz::Array<double, 2>& Lat,
	      const blitz::Array<double, 2>& Lon);
  boost::shared_ptr<GeoCal::MemoryRasterImage>
  project_surface(double Resolution=70.0) const;
  void project_surface_scan_arr(GeoCal::RasterImage& Data,
				int Start_line, int Number_line=-1) const;
  GeoCal::MapInfo cover(double Resolution=70.0) const;
  boost::shared_ptr<GeoCal::MemoryRasterImage>
  raster_cover(double Resolution=70.0) const;
  boost::shared_ptr<GeoCal::VicarLiteRasterImage>
  raster_cover_vicar(const std::string& Fname, double Resolution=70.0) const;
private:
  boost::shared_ptr<EcostressImageGroundConnection> igc_;
  bool include_angle;
  int nsub_line, nsub_sample;
  mutable blitz::Array<double, 5> res; // Cache of results for ground_coor_arr
  mutable blitz::Array<double, 3> dist; // Last distance we went with
					// ray casting
  mutable int sl, el;			// Start frame line and end
					// frame line for processing.
  // The ScLookVector is identical for all samples, so we calculate
  // once and cache
  blitz::Array<GeoCal::ScLookVector, 3> camera_slv;
  // These are redundant with igc_, but we stash these just to make
  // our code simpler.
  int b;			// Band we are working with
  boost::shared_ptr<GeoCal::Camera> cam;
  boost::shared_ptr<EcostressTimeTable> tt;
  void init();
  void ground_coor_arr_samp(int Start_line, int Sample,
			    bool initial_samp = false) const;
  GroundCoordinateArray() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  template<class Archive>
  void save(Archive & ar, const unsigned int version) const;
  template<class Archive>
  void load(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::GroundCoordinateArray);
#endif

  
  
