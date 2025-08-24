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
/// We have this in geocal as
/// 4630b700ebbf6a9f22b5ab1cb5717fd01f718863,
/// but leave this here for now so we can work with older version of geocal
//-----------------------------------------------------------------------

void Ecostress::set_fill_value(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Fill_value)
{
  Img->raster_band().SetNoDataValue(Fill_value);
}

//-----------------------------------------------------------------------
/// We have this in geocal as
/// 4630b700ebbf6a9f22b5ab1cb5717fd01f718863,
/// but leave this here for now so we can work with older version of geocal
//-----------------------------------------------------------------------

void Ecostress::set_scale(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Scale_value)
{
  Img->raster_band().SetScale(Scale_value);
}

//-----------------------------------------------------------------------
/// We have this in geocal as
/// 4630b700ebbf6a9f22b5ab1cb5717fd01f718863,
/// but leave this here for now so we can work with older version of geocal
//-----------------------------------------------------------------------

void Ecostress::set_offset(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, double Offset_value)
{
  Img->raster_band().SetOffset(Offset_value);
}

//-----------------------------------------------------------------------
/// Fixed in geocal 01dbca8b51048e80102bb70032561bf479a035a9. Leave
/// this in place since we already have it, just so we work with older
/// version of geocal.
//-----------------------------------------------------------------------

void Ecostress::write_data(const boost::shared_ptr<GeoCal::GdalRasterImage>& Img, const blitz::Array<double, 2>& Data)
{
  Img->write(0,0,Data);
}


//-----------------------------------------------------------------------
/// We have this in geocal as
/// 4630b700ebbf6a9f22b5ab1cb5717fd01f718863,
/// but leave this here for now so we can work with older version of geocal
//-----------------------------------------------------------------------


void Ecostress::write_gdal(const std::string& Fname, const std::string& Driver_name,
			   const GeoCal::GdalRasterImage& Img, const std::string& Options)
{
  GeoCal::gdal_create_copy(Fname, Driver_name, *Img.data_set(), Options);
}

//-----------------------------------------------------------------------
/// We have this in geocal as
/// 4630b700ebbf6a9f22b5ab1cb5717fd01f718863,
/// but leave this here for now so we can work with older version of geocal
//-----------------------------------------------------------------------

std::string Ecostress::to_proj4(const boost::shared_ptr<GeoCal::OgrCoordinate>& G)
{
  char *res;
  G->ogr().ogr().exportToProj4(&res);
  std::string ress(res);
  CPLFree(res);
  return ress;
}
