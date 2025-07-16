#include "resampler.h"
#include "ecostress_serialize_support.h"
#include "ecostress_dqi.h"
#include "geocal/magnify_replicate.h"
#include "geocal/magnify_bilinear.h"
#include "geocal/geodetic.h"
#include "geocal/vicar_raster_image.h"
#include <boost/make_shared.hpp>
#include <cmath>
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
/// Constructor. This takes the latitude (Y) and longitude (X) fields as
/// RasterImage (we could have taken the L1B_GEO file name, but taking
/// RasterImage seems a little more general). We take the MapInfo that
/// we will resample to (you can get that from something like
/// mi = Landsat7Global("/raid22",Landsat7Global.BAND5).map_info.scale(2,2)
/// in python).
///
/// For a geodetic map, this is longitude (X) and latitude (Y). For
/// other map projections, this is just the general X and Y
/// coordinates. Note that these should already be converted to the
/// coordinate system of the map info.
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
(const boost::shared_ptr<GeoCal::RasterImage>& X_coor,
 const boost::shared_ptr<GeoCal::RasterImage>& Y_coor,
 const GeoCal::MapInfo& Mi, int Num_sub_pixel, bool Exactly_match_mi,
 double Mark_missing)
  : nsub(Num_sub_pixel)
{
  MagnifyBilinear xmag(X_coor, Num_sub_pixel);
  MagnifyBilinear ymag(Y_coor, Num_sub_pixel);
  blitz::Array<double, 2> x = xmag.read_double(0,0, xmag.number_line(),
					       xmag.number_sample());
  blitz::Array<double, 2> y = ymag.read_double(0,0, ymag.number_line(),
					       ymag.number_sample());
  init(x, y, Mi, Exactly_match_mi, Mark_missing);
}

//-------------------------------------------------------------------------
/// Alternative constructor where we get the lat/lon from something
/// other than a file. The data should already be interpolated (e.g.,
/// in python do scipy.ndimage.interpolation.zoom(t,Num_sub_pixel,order=2)
//-------------------------------------------------------------------------

Resampler::Resampler
(const blitz::Array<double, 2>& X_coor_interpolated,
 const blitz::Array<double, 2>& Y_coor_interpolated,
 const GeoCal::MapInfo& Mi, int Num_sub_pixel, bool Exactly_match_mi,
 double Mark_missing)
  : nsub(Num_sub_pixel)
{
  init(X_coor_interpolated, Y_coor_interpolated, Mi, Exactly_match_mi, Mark_missing);
}

void Resampler::init(const blitz::Array<double, 2>& X_coor,
		     const blitz::Array<double, 2>& Y_coor,
		     const GeoCal::MapInfo& Mi, bool Exactly_match_mi,
		     double Mark_missing)
{
  blitz::Range ra = blitz::Range::all();

  data_index.resize(X_coor.rows(), X_coor.cols(), 2);
  blitz::Array<double, 2> xindex, yindex;
  Mi.coordinate_to_index(X_coor, Y_coor, xindex, yindex);
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
  for(int i = 0; i < X_coor.rows(); ++i)
    for(int j = 0; j < X_coor.cols(); ++j)
      if(Y_coor(i, j) > Mark_missing && X_coor(i, j) > Mark_missing) {
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
  for(int i = 0; i < X_coor.rows(); ++i)
    for(int j = 0; j < X_coor.cols(); ++j)
      if(Y_coor(i, j) <= Mark_missing && X_coor(i, j) <= Mark_missing)
	data_index(i,j,ra) = -9999;
}

//-------------------------------------------------------------------------
/// Had an issue with python pool hanging. Not sure of the exact
/// reason, but we tracked this down to some resource not being
/// released. As a simple workaround, have a clear function that
/// empties data_index. You wouldn't normally call this, but we do in
/// python to work around this python multiprocessing pool issue.
///
/// ** Note this ended up being a red herring, and we don't actually use
/// this anymore. However leave this place in case we end up needing
/// come back to this **
//-------------------------------------------------------------------------

void Resampler::clear()
{
  blitz::Array<int, 3> empty;
  data_index.reference(empty);
  std::cerr << "Cleared data\n";
}

//-------------------------------------------------------------------------
/// Determine range of X and Y coordinate arrays that actually touch
/// the given MapInfo. Used when we are producing the tiled product
/// where lots of the data isn't even used and can be skipped before
/// we even start.
//-------------------------------------------------------------------------

void Resampler::determine_range(const blitz::Array<double, 2>& X_coor_interpolated,
				const blitz::Array<double, 2>& Y_coor_interpolated,
				const GeoCal::MapInfo& Mi, int Num_sub_pixel,
				int& lstart, int& lend, int& sstart, int& send)
{
  lstart = X_coor_interpolated.rows();
  lend = -1;
  sstart = X_coor_interpolated.cols();
  send = -1;
  blitz::Array<double, 2> xindex, yindex;
  Mi.coordinate_to_index(X_coor_interpolated, Y_coor_interpolated, xindex, yindex);
  for(int i = 0; i < xindex.rows(); ++i)
    for(int j = 0; j < xindex.cols(); ++j) {
      int ln = (int) std::round(yindex(i,j));
      int smp = (int) std::round(xindex(i,j));
      if(ln >= 0 && ln < Mi.number_y_pixel() &&
	 smp >=0 && smp < Mi.number_x_pixel()) {
	lstart = std::min(lstart, i);
	lend = std::max(lend, i);
	sstart = std::min(sstart, j);
	send = std::max(send, j);
      }
    }
  // Tweak to make divisible by Num_sub_pixel
  lstart = std::floor(double(lstart) / Num_sub_pixel) * Num_sub_pixel;
  lend = std::ceil(double(lend) / Num_sub_pixel) * Num_sub_pixel;
  sstart = std::floor(double(sstart) / Num_sub_pixel) * Num_sub_pixel;
  send = std::ceil(double(send) / Num_sub_pixel) * Num_sub_pixel;
}

//-------------------------------------------------------------------------
/// Check to see if we will have any data fall with the MapInfo.
//-------------------------------------------------------------------------

bool Resampler::empty_resample() const
{
  for(int i = 0; i < data_index.rows(); ++i)
    for(int j = 0; j < data_index.cols(); ++j) {
      int ln, smp;
      ln = data_index(i,j,0);
      smp = data_index(i,j,1);
      if(ln >= 0 && ln < mi.number_y_pixel() &&
	 smp >=0 && smp < mi.number_x_pixel())
	return false;
    }
  return true;
}

//-------------------------------------------------------------------------
/// Check to see if we will have any data fall with the
/// MapInfo. Checks a field also to exclude fill data
//-------------------------------------------------------------------------

bool Resampler::empty_resample(const boost::shared_ptr<GeoCal::RasterImage>& Data) const
{
  MagnifyReplicate datamag(Data, nsub);
  for(int i = 0; i < data_index.rows(); ++i)
    for(int j = 0; j < data_index.cols(); ++j) {
      int ln, smp;
      ln = data_index(i,j,0);
      smp = data_index(i,j,1);
      if(ln >= 0 && ln < mi.number_y_pixel() &&
	 smp >=0 && smp < mi.number_x_pixel() &&
	 datamag(i,j) > fill_value_threshold)
	return false;
    }
  return true;
}

//-------------------------------------------------------------------------
/// Resample the given data and return an array of values.
///
/// We can scale the data by the given factor, optionally clip
/// negative values to 0, and specify the fill_value to use for data
/// that we don't see.
///
/// For some data, averaging the values that hit a grid cell doesn't
/// actually make sense (e.g., for view angles). You can instead
/// specify Use_smallest_ic which uses the value for the smallest
/// line/sample that sees a particular grid cell.
//-------------------------------------------------------------------------

blitz::Array<double, 2> Resampler::resample_field
(const boost::shared_ptr<GeoCal::RasterImage>& Data,
 double Scale_data, bool Negative_to_zero, double Fill_value,
 bool Use_smallest_ic) const
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
  // d and data_index should be the same size, but check this.
  if(d.rows() < data_index.rows() ||
     d.cols() < data_index.cols()) {
    Exception e;
    e << "data_index should be larger than magnified data\n"
      << "d:          " << d.rows() << " x " << d.cols() << "\n"
      << "data_index: " << data_index.rows() << " x " << data_index.cols()
      << "\n";
    throw e;
  }
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
	  // Add data, unless we already have data there and
	  // Use_smallest_ic is true
	  if(!Use_smallest_ic || cnt(ln,smp) == 0) {
	    res(ln,smp) += d(i,j);
	    cnt(ln,smp) += 1;
	  }
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
/// Resample the DQI field.
///
/// The DQI is initially set to DQI_NOT_SEEN. We then go through all
/// the pixels and use the following logic:
///
/// 1. If we encounter DQI_INTERPOLATED, we set the DQI to this value.
/// 2. If we encounter DQI_BAD_OR_MISSING and the DQI is currently
///     DQI_NOT_SEEN then we set it to DQI_BAD_OR_MISSING.
/// 3. If we encounter DQI_STRIPE_NOT_INTERPOLATED and the the DQI is
///    currently DQI_NOT_SEEN then we set it to
///    DQI_STRIPE_NOT_INTERPOLATED.
/// 4. If we encounter DQI_GOOD and the DQI is anything other than
///    DQI_INTERPOLATED we set it to this value.
//-------------------------------------------------------------------------

blitz::Array<int, 2> Resampler::resample_dqi
(const boost::shared_ptr<GeoCal::RasterImage>& Data) const
{
  // We do replication here since we are counting subpixels. This is
  // particularly important to get the fill values correct.
  MagnifyReplicate datamag(Data, nsub);
  blitz::Array<int, 2> d = datamag.read(0,0, datamag.number_line(),
					datamag.number_sample());
  blitz::Array<int, 2> res(mi.number_y_pixel(), mi.number_x_pixel());
  res = DQI_NOT_SEEN;
  for(int i = 0; i < data_index.rows(); ++i)
    for(int j = 0; j < data_index.cols(); ++j) {
      int ln, smp;
      ln = data_index(i,j,0);
      smp = data_index(i,j,1);
      if(ln >= 0 && ln < res.rows() &&
	 smp >=0 && smp < res.cols()) {
// 1. If we encounter DQI_INTERPOLATED, we set the DQI to this value.
// 2. If we encounter DQI_BAD_OR_MISSING and the DQI is currently
//     DQI_NOT_SEEN then we set it to DQI_BAD_OR_MISSING.
// 3. If we encounter DQI_STRIPE_NOT_INTERPOLATED and the the DQI is
//    currently DQI_NOT_SEEN then we set it to
//    DQI_STRIPE_NOT_INTERPOLATED.
// 4. If we encounter DQI_GOOD and the DQI is anything other than
//    DQI_INTERPOLATED we set it to this value.
	if(d(i,j) == DQI_INTERPOLATED)
	  res(ln,smp) = DQI_INTERPOLATED;
	if(d(i,j) == DQI_BAD_OR_MISSING && res(ln,smp) == DQI_NOT_SEEN)
	  res(ln,smp) = DQI_BAD_OR_MISSING;
	if(d(i,j) == DQI_STRIPE_NOT_INTERPOLATED &&
	   res(ln,smp) == DQI_NOT_SEEN)
	  res(ln,smp) = DQI_STRIPE_NOT_INTERPOLATED;
	if(d(i,j) == DQI_GOOD && res(ln,smp) != DQI_INTERPOLATED)
	  res(ln,smp) = DQI_GOOD;
      } 
    }
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
      boost::shared_ptr<GroundCoordinate> gp = mi.ground_coordinate(j, i, d);
      gp->lat_lon_height(Lat(i,j), Lon(i,j), Height(i,j));
    }
}

