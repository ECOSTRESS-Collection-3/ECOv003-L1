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
