#include "ground_coordinate_array.h"
#include "ecostress_serialize_support.h"
#include "geocal/ostream_pad.h"

using namespace Ecostress;

template<class Archive>
void GroundCoordinateArray::save(Archive & ar, const unsigned int version) const
{
  // Nothing more to do
}

template<class Archive>
void GroundCoordinateArray::load(Archive & ar, const unsigned int version)
{
  init();
}

template<class Archive>
void GroundCoordinateArray::serialize(Archive & ar, const unsigned int version)
{
  ECOSTRESS_GENERIC_BASE(GroundCoordinateArray);
  ar & GEOCAL_NVP_(igc)
    & GEOCAL_NVP(include_angle);
  boost::serialization::split_member(ar, *this, version);
}

ECOSTRESS_IMPLEMENT(GroundCoordinateArray);

inline double sqr(double x) { return x * x; }

void GroundCoordinateArray::init()
{
  b = igc_->band();
  cam = igc_->camera();
  tt = boost::dynamic_pointer_cast<EcostressTimeTable>(igc_->time_table());
  if(!tt)
    throw GeoCal::Exception("GroundCoordinateArray only works with EcostressTimeTable");
  int nl = cam->number_line(b);
  if(tt->averaging_done())
    for(int i = 0; i < nl; ++i)
      camera_slv.push_back(cam->sc_look_vector(GeoCal::FrameCoordinate(2*i, 0), b));
  else
    for(int i = 0; i < nl; ++i)
      camera_slv.push_back(cam->sc_look_vector(GeoCal::FrameCoordinate(i, 0), b));
  dist.resize((int) camera_slv.size());
  res.resize((int) camera_slv.size(), igc_->number_sample(),
	     (include_angle ? 7 : 3));
}

//-------------------------------------------------------------------------
/// Create a MemoryRasterImage that matches cover(), and fill it in
/// with 0 fill data.
//-------------------------------------------------------------------------

boost::shared_ptr<GeoCal::MemoryRasterImage>
GroundCoordinateArray::raster_cover(double Resolution) const
{
  boost::shared_ptr<GeoCal::MemoryRasterImage> res =
    boost::make_shared<GeoCal::MemoryRasterImage>(cover(Resolution));
  res->data()(blitz::Range::all(), blitz::Range::all()) = 0;
  return res;
}

//-------------------------------------------------------------------------
/// Calculate the map info to cover the ground projection of the
/// Igc. This is like what the python program igc_project calculates,
/// but it is more convenient to have this in C++ here.
/// The Resolution is in meters.
//-------------------------------------------------------------------------

GeoCal::MapInfo GroundCoordinateArray::cover(double Resolution) const
{
  // Copy of what cib01_mapinfo() does
  blitz::Array<double, 1> parm(6);
  parm = -120.00609312061941, 9.2592593000000006e-06, 0,
    47.011777984629603, 0, -9.2592593000000006e-06;
  GeoCal::MapInfo cib01(boost::make_shared<GeoCal::GeodeticConverter>(), parm,
		27109425, 8795732);
  double resbase = cib01.resolution_meter();
  GeoCal::MapInfo cib01_scaled = cib01.scale(Resolution / resbase,
				     Resolution / resbase);
  return igc_->cover(cib01_scaled);
}

//-------------------------------------------------------------------------
/// This projects the Igc to the surface for a single scan array. We
/// fill in Ras with whatever the last encountered value is, i.e. we
/// make no attempt to average data. We could implement averaging if
/// needed, but for right now we just put in the value.
///
/// We do nothing with points that we don't see, so if for example you
/// want a fill value you should make sure to fill in Data before
/// calling this function.
//-------------------------------------------------------------------------

void GroundCoordinateArray::project_surface_scan_arr
(GeoCal::RasterImage& Data, int Start_line, int Number_line) const
{
  blitz::Array<double,3> gp = ground_coor_scan_arr(Start_line, Number_line);
  for(int i = 0; i < gp.rows(); ++i)
    for(int j = 0; j < gp.cols(); ++j) {
      GeoCal::ImageCoordinate ic = Data.coordinate(GeoCal::Geodetic(gp(i,j,0),
								    gp(i,j,1)));
      int ln = (int) floor(ic.line + 0.5);
      int smp = (int) floor(ic.sample + 0.5);
      if(ln >= 0 && ln < Data.number_line() && smp >= 0 &&
	 smp < Data.number_sample() && Start_line + i < igc_->number_line()) {
	int val = igc_->image()->read(Start_line + i, j);
	if(val > -9998)
	  Data.write(ln, smp, val);
      }
    }
}

//-------------------------------------------------------------------------
/// This interpolates the given RasterImage at the given latitude,
/// longitude locations. This is exactly the same as calling
/// Data.interpolate(Data.coordinate(Geodetic(Lat,Lon)) repeatedly,
/// except this runs much faster than doing this operation in python.
//-------------------------------------------------------------------------

blitz::Array<double, 2> GroundCoordinateArray::interpolate
(const GeoCal::RasterImage& Data,
 const blitz::Array<double, 2>& Lat,
 const blitz::Array<double, 2>& Lon)
{
  blitz::Array<double, 2> res(Lat.rows(), Lat.cols());
  if(Lat.rows() != Lon.rows() || Lat.cols() != Lon.cols())
    throw GeoCal::Exception("Lat and Lon need to be the same size");
  for(int i = 0; i < res.rows(); ++i)
    for(int j = 0; j < res.cols(); ++j)
      res(i,j) = Data.interpolate(Data.coordinate(GeoCal::Geodetic(Lat(i,j), Lon(i,j))));
  return res;
}
//-------------------------------------------------------------------------
/// This returns the ground coordinates for every pixel in the
/// ImageGroundConnection as a number_line x number_sample x 3 array,
/// with the coordinates as latitude, longitude, height. These are the
/// same values that you would get from just repeatedly calling
/// igc()->ground_coordinate(ic), but we take advantage of the special
/// form of the Ecostress scan to speed up this calculation a lot.
///
/// If include_angle was specified in the construtor, we return a
/// number_line x number_sample x 7 array with coordinates as
/// latitude, longitude, height, view_zenith, view_azimuth,
/// solar_zenith, solar_azimuth.
//-------------------------------------------------------------------------

blitz::Array<double,3> GroundCoordinateArray::ground_coor_arr() const
{
  blitz::Array<double, 3> r(igc_->number_line(), igc_->number_sample(), 3);
  for(int i = 0; i < tt->number_scan(); ++i) {
    int lstart, lend;
    tt->scan_index_to_line(i, lstart, lend);
    r(blitz::Range(lstart, lend-1), blitz::Range::all(), blitz::Range::all()) =
      ground_coor_scan_arr(lstart, lend-lstart);
  }
  return res;
}

//-------------------------------------------------------------------------
/// This return the ground coordinates as a number_line x
/// number_sample x 3 array, with the coordinates as latitude,
/// longitude, and height. You don't normally call this function,
/// instead you likely want ground_coor_arr. We have this function
/// exposed to aid with testing - it is quicker to call this for a
/// single scan rather than doing all the scans like ground_coor_arr.
/// Also, in python if we are doing parallel processing we can do each
/// ground_coor_arr separately if desired.
///
/// If include_angle was specified in the construtor, we return a
/// number_line x number_sample x 7 array with coordinates as
/// latitude, longitude, height, view_zenith, view_azimuth,
/// solar_zenith, solar_azimuth.
//-------------------------------------------------------------------------

blitz::Array<double,3>
GroundCoordinateArray::ground_coor_scan_arr
(int Start_line, int Number_line) const
{
  int ms = igc_->number_sample() / 2;
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc;
  tt->time(GeoCal::ImageCoordinate(Start_line, ms), t, fc);
  if(tt->averaging_done())
    sl = (int) floor(fc.line / 2 + 0.5);
  else
    sl = (int) floor(fc.line + 0.5);
  if(Number_line < 0)
    el = (int) tt->number_line_scan();
  else
    el = std::min(sl + Number_line, (int) tt->number_line_scan());
  ground_coor_arr_samp(Start_line, ms, true);
  blitz::Array<double, 1> dist_middle(dist.copy());
  for(int smp = ms + 1; smp < igc_->number_sample(); ++smp)
    ground_coor_arr_samp(Start_line, smp);
  dist = dist_middle;
  for(int smp = ms - 1; smp >= 0; --smp)
    ground_coor_arr_samp(Start_line, smp);
  return blitz::Array<double, 3>(res(blitz::Range(sl, el-1),
				     blitz::Range::all(),
				     blitz::Range::all()));
}

void GroundCoordinateArray::ground_coor_arr_samp(int Start_line, int Sample,
						 bool Initial_samp) const
{
  using namespace GeoCal;
  Time t;
  FrameCoordinate fc;
  tt->time(ImageCoordinate(Start_line, Sample), t, fc);
  boost::shared_ptr<QuaternionOrbitData> od =
    igc_->orbit_data(t, Sample);
  boost::shared_ptr<CartesianFixed> cf = od->position_cf();
  CartesianFixedLookVector slv;
  if(include_angle)
    slv = CartesianFixedLookVector::solar_look_vector(t);
  for(int i = sl; i < el; ++i) {
    CartesianFixedLookVector lv = od->cf_look_vector(camera_slv[i]);
    boost::shared_ptr<CartesianFixed> pt;
    if(Initial_samp)
      pt = igc_->dem().intersect(*cf, lv, igc_->resolution(), igc_->max_height());
    else {
      double start_dist = dist(i);
      if(i - 1 >= sl)
	start_dist = std::min(start_dist, dist(i-1));
      if(i + 1 < el)
	start_dist = std::min(start_dist, dist(i+1));
      pt = igc_->dem().intersect_start_length(*cf, lv, igc_->resolution(),
					     start_dist);
    }
    pt->lat_lon_height(res(i, Sample, 0), res(i, Sample, 1), res(i, Sample, 2));
    dist(i) = sqrt(sqr(pt->position[0] - cf->position[0]) +
		   sqr(pt->position[1] - cf->position[1]) +
		   sqr(pt->position[2] - cf->position[2]));
    if(include_angle) {
      LnLookVector vln(CartesianFixedLookVector(*pt,*cf),*pt);
      res(i,Sample,3) = vln.view_zenith();
      res(i,Sample, 4) = vln.view_azimuth();
      LnLookVector sln(slv, *pt);
      res(i,Sample,5) = sln.view_zenith();
      res(i,Sample, 6) = sln.view_azimuth();
    }
  }
}

void GroundCoordinateArray::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "GroundCoordinateArray:\n";
  Os << "  Igc:\n";
  opad << *igc_;
  opad.strict_sync();
}
  
