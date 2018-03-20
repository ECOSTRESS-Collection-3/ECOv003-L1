#include "resampler.h"
#include "ecostress_serialize_support.h"
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
//-------------------------------------------------------------------------
Resampler::Resampler
(const boost::shared_ptr<GeoCal::RasterImage>& Latitude,
 const boost::shared_ptr<GeoCal::RasterImage>& Longitude,
 const GeoCal::MapInfo& Mi, int Num_sub_pixel)
  : nsub(Num_sub_pixel)
{
  blitz::Range ra = blitz::Range::all();
  MagnifyBilinear latmag(Latitude, Num_sub_pixel);
  MagnifyBilinear lonmag(Longitude, Num_sub_pixel);
  blitz::Array<double, 2> lat = latmag.read_double(0,0, latmag.number_line(),
						   latmag.number_sample());
  blitz::Array<double, 2> lon = lonmag.read_double(0,0, lonmag.number_line(),
						   lonmag.number_sample());
  std::vector<boost::shared_ptr<GroundCoordinate> > ptlist;
  ptlist.push_back(boost::make_shared<Geodetic>(blitz::min(lat),
						blitz::min(lon)));
  ptlist.push_back(boost::make_shared<Geodetic>(blitz::max(lat),
						blitz::max(lon)));
  mi = Mi.cover(ptlist);
  double latstart, lonstart;
  double latdelta, londelta;
  mi.index_to_coordinate(0,0,lonstart,latstart);
  mi.index_to_coordinate(1,1,londelta,latdelta);
  latdelta -= latstart;
  londelta -= lonstart;
  data_index.resize(lat.rows(), lon.cols(), 2);
  data_index(ra,ra,0) = blitz::cast<int>(blitz::rint((lat-latstart)/latdelta));
  data_index(ra,ra,1) = blitz::cast<int>(blitz::rint((lon-lonstart)/londelta));
}

//-------------------------------------------------------------------------
/// Resample the given data, and write out to a VICAR file with the
/// given name
//-------------------------------------------------------------------------

void Resampler::resample_field
(const std::string& Fname,
 const boost::shared_ptr<GeoCal::RasterImage>& Data)
{
  MagnifyBilinear datamag(Data, nsub);
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
      if(d(i,j) > -9998) {
	res(ln,smp) += d(i,j);
	cnt(ln,smp) += 1;
      }
    }
  res = blitz::where(cnt == 0, 0, res / cnt);
  VicarRasterImage f(Fname, mi, "REAL");
  f.write(0,0,res);
}


