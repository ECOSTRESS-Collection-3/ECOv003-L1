#include "coordinate_convert.h"
using namespace Ecostress;


//-----------------------------------------------------------------------
/// This is a bulk conversion from latitude/longitude to a different
/// set of coordinates.
//-----------------------------------------------------------------------

blitz::Array<double, 2> Ecostress::coordinate_convert
(const blitz::Array<double, 1>& latitude,
 const blitz::Array<double, 1>& longitude,
 const boost::shared_ptr<GeoCal::OgrWrapper>& ogr)
{
  blitz::Range ra = blitz::Range::all();
  if(latitude.rows() != longitude.rows())
    throw GeoCal::Exception("latitude and longitude need to be the same size");
  blitz::Array<double, 1> x = longitude.copy();
  blitz::Array<double, 1> y = latitude.copy();
  const_cast<OGRCoordinateTransformation*>(ogr->inverse_transform())->Transform(latitude.rows(), &x(0), &y(0));
  blitz::Array<double, 2> res(x.rows(), 2);
  res(ra,0) = x;
  res(ra,1) = y;
  return res;
}

//-----------------------------------------------------------------------
/// This really belongs in geocal, but stick here for now. We will
/// probably eventually migrate this to geocal.
//-----------------------------------------------------------------------

void Ecostress::set_fill_value(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Fill_value)
{
  Img->raster_band().SetNoDataValue(Fill_value);
}

//-----------------------------------------------------------------------
/// This really belongs in geocal, but stick here for now. We will
/// probably eventually migrate this to geocal. The actual
/// GdalRasterImage already handles writing double data, but we hadn't 
/// put this into the python swig wrappers. No reason, just an
/// oversight that never came up until now.

//-----------------------------------------------------------------------

void Ecostress::write_data(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, const blitz::Array<double, 2>& Data)
{
  Img->write(0,0,Data);
}


//-----------------------------------------------------------------------
/// This really belongs in geocal, but stick here for now. We will
/// probably eventually migrate this to geocal. This handles drivers
/// that only support create_copy (like COG). We create using a
/// different driver, often "MEM", and then pass to this to create the
/// output file.
//-----------------------------------------------------------------------


void Ecostress::write_gdal(const std::string& Fname, const std::string& Driver_name,
			   const GeoCal::GdalRasterImage& Img, const std::string& Options)
{
  GeoCal::gdal_create_copy(Fname, Driver_name, *Img.data_set(), Options);
}

