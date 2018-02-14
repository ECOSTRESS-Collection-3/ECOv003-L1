#include "simulated_radiance.h"
#include "ecostress_serialize_support.h"
#include "raster_averaged.h"
#include "memory_raster_image.h"
#include "geocal/ostream_pad.h"

using namespace Ecostress;

template<class Archive>
void SimulatedRadiance::save(Archive & ar, const unsigned int version) const
{
  // Nothing more to do
}

template<class Archive>
void SimulatedRadiance::load(Archive & ar, const unsigned int version)
{
  init();
}

template<class Archive>
void SimulatedRadiance::serialize(Archive & ar, const unsigned int version)
{
  ECOSTRESS_GENERIC_BASE(SimulatedRadiance);
  ar & GEOCAL_NVP_(gca)
    & GEOCAL_NVP_(avg_factor) & GEOCAL_NVP_(read_into_memory)
    & GEOCAL_NVP_(fill_value) & GEOCAL_NVP_(img);
  boost::serialization::split_member(ar, *this, version);
}

ECOSTRESS_IMPLEMENT(SimulatedRadiance);

void SimulatedRadiance::init()
{
  if(avg_factor_ < 0)
    avg_factor_ = 
      (int) floor(gca_->igc()->resolution_meter() /
		  img_->map_info().resolution_meter());
  if(avg_factor_ > 1)
    img_avg_.reset(new GeoCal::RasterAveraged(img_, avg_factor_, avg_factor_));
  else
    img_avg_ = img_;
  if(read_into_memory_)
    img_avg_.reset(new GeoCal::MemoryRasterImage(*img_avg_));
}

//-------------------------------------------------------------------------
/// Call ground_coor_scan_arr, and then use the location to determine
/// the radiance we would see from the map_projected_image(). This is
/// for a single scan. We use this interface, because this is a good
/// unit for python to call while generating this in parallel. See
/// L1aPixSimulate for the use of this.
//-------------------------------------------------------------------------

blitz::Array<double, 2> SimulatedRadiance::radiance_scan
(int Start_line, int Number_line) const
{
  blitz::Array<double, 5> gcarr = gca_->ground_coor_scan_arr(Start_line, Number_line);
  blitz::Array<double, 2> res(gcarr.rows(), gcarr.cols());
  for(int i = 0; i < gcarr.rows(); ++i)
    for(int j = 0; j < gcarr.cols(); ++j) {
      GeoCal::Geodetic gc(gcarr(i,j,0,0,0),gcarr(i,j,0,0,1),gcarr(i,j,0,0,2));
      GeoCal::ImageCoordinate ic = img_avg_->coordinate(gc);
      if(ic.line < 0 || ic.line > img_avg_->number_line() - 1 ||
	 ic.sample < 0 || ic.sample > img_avg_->number_sample() - 1)
	res(i, j) = fill_value_;
      else
	res(i, j) = img_avg_->unchecked_interpolate(ic.line, ic.sample);
    }
  return res;
}

void SimulatedRadiance::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "SimulatedRadiance:\n"
     << "  Avg_factor:       " << avg_factor() << "\n"
     << "  Read into memory: " << (read_into_memory() ? "true" : "false") 
     << "\n"
     << "  Fill value:       " << fill_value() << "\n";
  Os << "  GroundCoordinateArray:\n";
  opad << *gca_;
  opad.strict_sync();
  Os << "  Map projected image:\n" ;
  opad << *img_ << "\n";
  opad.strict_sync();
}
