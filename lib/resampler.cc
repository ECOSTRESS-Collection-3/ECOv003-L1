#include "resampler.h"
#include "ecostress_serialize_support.h"
#include "ecostress_dqi.h"
#include "geocal/magnify_replicate.h"
#include "geocal/magnify_bilinear.h"
#include "geocal/geodetic.h"
#include "geocal/vicar_raster_image.h"
#include <boost/make_shared.hpp>
using namespace Ecostress;
using namespace GeoCal;

template<class Archive>
void Resampler::serialize(Archive & ar, const unsigned int version)
{
  ECOSTRESS_GENERIC_BASE(Resampler);
  ar & GEOCAL_NVP(mi)
    & GEOCAL_NVP(nsub)
    & GEOCAL_NVP(data_index);
}

ECOSTRESS_IMPLEMENT(Resampler);

//-------------------------------------------------------------------------
/// Constructor. This takes the latitude and longitude fields as
/// RasterImage (we could have taken the L1B_GEO file name, but taking
/// RasterImage seems a little more general). We take the MapInfo that
/// we will resample to (you can get that from something like
/// mi = Landsat7Global("/raid22",Landsat7Global.BAND5).map_info.scale(2,2)
/// in python).
///
/// We make sure the mapinfo covers the latitude/longitude range
///
/// We also pass in the number of subpixels to calculate, so for
/// example to work with 60 m landsat like map projection you'd want
/// this to be 2.
///
/// By default, we only use Mi to determine the pixel resolution, and
/// we make sure the output covers the full latitude/longitude
/// range. You can optionally specify that we exactly match the passed
/// in Mi, regardless of the actually coverage of the lat/lon. This is
/// useful if we are producing output files to compare against some
/// existing file.
//-------------------------------------------------------------------------

Resampler::Resampler
(const boost::shared_ptr<GeoCal::RasterImage>& Latitude,
 const boost::shared_ptr<GeoCal::RasterImage>& Longitude,
 const GeoCal::MapInfo& Mi, int Num_sub_pixel, bool Exactly_match_mi)
  : nsub(Num_sub_pixel)
{
  MagnifyBilinear latmag(Latitude, Num_sub_pixel);
  MagnifyBilinear lonmag(Longitude, Num_sub_pixel);
  blitz::Array<double, 2> lat = latmag.read_double(0,0, latmag.number_line(),
						   latmag.number_sample());
  blitz::Array<double, 2> lon = lonmag.read_double(0,0, lonmag.number_line(),
						   lonmag.number_sample());
  init(lat, lon, Mi, Exactly_match_mi);
}

//-------------------------------------------------------------------------
/// Alternative constructor where we get the lat/lon from something
/// other than a file. The data should already be interpolated (e.g.,
/// in python do scipy.ndimage.interpolation.zoom(t,Num_sub_pixel,order=2)
//-------------------------------------------------------------------------

Resampler::Resampler
(const blitz::Array<double, 2>& Latitude_interpolated,
 const blitz::Array<double, 2>& Longitude_interpolated,
 const GeoCal::MapInfo& Mi, int Num_sub_pixel, bool Exactly_match_mi)
  : nsub(Num_sub_pixel)
{
  init(Latitude_interpolated, Longitude_interpolated, Mi, Exactly_match_mi);
}

void Resampler::init(const blitz::Array<double, 2>& lat,
		     const blitz::Array<double, 2>& lon,
		     const GeoCal::MapInfo& Mi, bool Exactly_match_mi)
{
  blitz::Range ra = blitz::Range::all();
  // As an optimization, we assume the map uses a
  // GeodeticConverter. We could relax this if needed, at the cost of
  // some speed. But for now, just assume this and trigger an error if
  // we don't have this.
  GeoCal::GeodeticConverter g;
  if(!Mi.coordinate_converter().is_same(g))
    throw GeoCal::Exception("Resampler only works with MapInfo that uses a GeodeticConverter");

  data_index.resize(lat.rows(), lon.cols(), 2);
  blitz::Array<double, 2> xindex, yindex;
  Mi.coordinate_to_index(lon, lat, xindex, yindex);
  data_index(ra,ra,0) = blitz::cast<int>(blitz::rint(yindex));
  data_index(ra,ra,1) = blitz::cast<int>(blitz::rint(xindex));
  if(Exactly_match_mi) {
    mi = Mi;
    return;
  }
  // Determine min and max xindex and yindex, but exclude all points
  // with lat/lon that are fill values.
  bool first = true;
  int minx = 0, miny = 0, maxx = 0, maxy = 0;
  for(int i = 0; i < lat.rows(); ++i)
    for(int j = 0; j < lat.cols(); ++j)
      if(lat(i, j) > -1000 && lon(i, j) > -1000) {
	if(first) {
	  minx = data_index(i,j,1);
	  miny = data_index(i,j,0);
	  maxx = minx;
	  maxy = miny;
	  first = false;
	}
	minx = std::min(data_index(i,j,1),minx);
	maxx = std::max(data_index(i,j,1),maxx);
	miny = std::min(data_index(i,j,0),miny);
	maxy = std::max(data_index(i,j,0),maxy);
      }
  mi = Mi.subset(minx, miny, maxx - minx + 1, maxy - miny + 1);
  data_index(ra,ra,0) -= miny;
  data_index(ra,ra,1) -= minx;
  // Make sure all the lat/lon fill values have data_index out of
  // range so we don't use the data.
  for(int i = 0; i < lat.rows(); ++i)
    for(int j = 0; j < lat.cols(); ++j)
      if(lat(i, j) <= -1000 && lon(i, j) <= -1000)
	data_index(i,j,ra) = -9999;
}

//-------------------------------------------------------------------------
/// Resample the given data and return an array of values
//-------------------------------------------------------------------------

blitz::Array<double, 2> Resampler::resample_field
(const boost::shared_ptr<GeoCal::RasterImage>& Data,
 double Scale_data, bool Negative_to_zero, double Fill_value) const
{
  // We do replication here since we are counting subpixels. This is
  // particularly important to get the fill values correct.
  MagnifyReplicate datamag(Data, nsub);
  blitz::Array<double, 2> d = datamag.read_double(0,0, datamag.number_line(),
						  datamag.number_sample());
  blitz::Array<double, 2> res(mi.number_y_pixel(), mi.number_x_pixel());
  blitz::Array<int, 2> cnt(res.shape());
  res = 0.0;
  cnt = 0;
  for(int i = 0; i < data_index.rows(); ++i)
    for(int j = 0; j < data_index.cols(); ++j) {
      int ln, smp;
      ln = data_index(i,j,0);
      smp = data_index(i,j,1);
      if(ln >= 0 && ln < cnt.rows() &&
	 smp >=0 && smp < cnt.cols()) {
	if(d(i,j) > fill_value_threshold) {
	  // Clear out any fill value we may have set
	  if(cnt(ln,smp) == 0)
	    res(ln,smp) = 0.0;
	  res(ln,smp) += d(i,j);
	  cnt(ln,smp) += 1;
	} else {
	  // Populate with fill value if we don't already have data
	  if(cnt(ln, smp) == 0) {
	    if(res(ln, smp) > fill_value_threshold)
	      res(ln, smp) = d(i,j);
	    else
	      res(ln, smp) = std::max(res(ln, smp), d(i,j));
	  }
	}
      }
    }
  res = blitz::where(cnt == 0, Fill_value, res / cnt * Scale_data);
  if(Negative_to_zero)
    res = blitz::where(res < 0, 0, res);
  return res;
}

//-------------------------------------------------------------------------
/// Resample the given data, and write out to a VICAR file with the
/// given name.
///
/// You can optionally scale the output data, and specify the file
/// output type to write. This is useful if you want to view float
/// data in xvd, which works much better with scaled int.
///
/// You can optionally map all negative values to zero, useful to view
/// data without large negative fill values (e.g., -9999)
//-------------------------------------------------------------------------

void Resampler::resample_field
(const std::string& Fname,
 const boost::shared_ptr<GeoCal::RasterImage>& Data,
 double Scale_data, const std::string& File_type, bool Negative_to_zero,
 double Fill_value) const
{
  blitz::Array<double, 2> res(resample_field(Data, Scale_data, Negative_to_zero,
					     Fill_value));
  VicarRasterImage f(Fname, mi, File_type);
  f.write(0,0,res);
}


//-------------------------------------------------------------------------
/// Various fields from the map_info. This is just all in a function
/// because this is much faster to do in C++ vs. looping in python.
//-------------------------------------------------------------------------

void Resampler::map_values
(const GeoCal::Dem& d,
 blitz::Array<double, 2>& Lat, blitz::Array<double, 2>& Lon,
 blitz::Array<double, 2>& Height) const
{
  Lat.resize(mi.number_y_pixel(), mi.number_x_pixel());
  Lon.resize(Lat.shape());
  Height.resize(Lat.shape());
  for(int i = 0; i < Lat.rows(); ++i)
    for(int j = 0; j < Lat.cols(); ++j) {
      boost::shared_ptr<GroundCoordinate> gp = mi.ground_coordinate(i, j, d);
      gp->lat_lon_height(Lat(i,j), Lon(i,j), Height(i,j));
    }
}

