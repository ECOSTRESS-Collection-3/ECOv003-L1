#ifndef RESAMPLER_H
#define RESAMPLER_H
#include "geocal/raster_image.h"
#include "geocal/dem.h"

namespace Ecostress {
/****************************************************************//**
  This is used to take the L1B_GEO latitude and longitude fields and
  project data to a given MapInfo.

  This is a bit brute force, and we don't worry about memory usage. 
  The arrays are something like 10Kx10K floating point, so we are
  talking GB but not 10's of GB. Since this is something we only run
  occasionally, this memory usage is probably fine. But if this
  becomes an issue, we can revisit this and make this code more
  efficient - but for now this doesn't seem to be worth the effort.
*******************************************************************/

class Resampler : public GeoCal::Printable<Resampler> {
public:
  Resampler(const boost::shared_ptr<GeoCal::RasterImage>& Latitude,
	    const boost::shared_ptr<GeoCal::RasterImage>& Longitude,
	    const GeoCal::MapInfo& Mi, int Num_sub_pixel = 2,
	    bool Exactly_match_mi = false);
  Resampler(const blitz::Array<double, 2>& Latitude_interpolated,
	    const blitz::Array<double, 2>& Longitude_interpolated,
	    const GeoCal::MapInfo& Mi, int Num_sub_pixel = 2,
	    bool Exactly_match_mi = false);
  virtual ~Resampler() {}
  const GeoCal::MapInfo& map_info() const { return mi; }
  int number_sub_pixel() const {return nsub; }
  blitz::Array<double, 2> resample_field
  (const boost::shared_ptr<GeoCal::RasterImage>& Data,
   double Scale_data=1.0,
   bool Negative_to_zero=false, double Fill_value = 0.0) const;
  void resample_field(const std::string& Fname,
		      const boost::shared_ptr<GeoCal::RasterImage>& Data,
		      double Scale_data=1.0,
		      const std::string& File_type="REAL",
		      bool Negative_to_zero=false, double Fill_value = 0.0) const;
  void map_values(const GeoCal::Dem& d,
		  blitz::Array<double, 2>& Lat, blitz::Array<double, 2>& Lon,
		  blitz::Array<double, 2>& Height) const;
  virtual void print(std::ostream& Os) const
  { Os << "ECOSTRESS Resampler";}
private:
  void init(const blitz::Array<double, 2>& lat,
	    const blitz::Array<double, 2>& lon,
	    const GeoCal::MapInfo& Mi, bool Exactly_match_mi);
  GeoCal::MapInfo mi;
  int nsub;
  blitz::Array<int, 3> data_index;
  Resampler() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
};

}

BOOST_CLASS_EXPORT_KEY(Ecostress::Resampler);
#endif
