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
  ar & GEOCAL_NVP_(igc);
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
  for(int i = 0; i < nl; ++i)
    camera_slv.push_back(cam->sc_look_vector(GeoCal::FrameCoordinate(i, 0), b));
  dist.resize((int) camera_slv.size());
  res.resize((int) camera_slv.size(), igc_->number_sample(),3);
}

//-------------------------------------------------------------------------
/// This returns the ground coordinates for every pixel in the
/// ImageGroundConnection as a number_line x number_sample x 3 array,
/// with the coordinates as latitude, longitude, height. These are the
/// same values that you would get from just repeatedly calling
/// igc()->ground_coordinate(ic), but we take advantage of the special
/// form of the Ecostress scan to speed up this calculation a lot.
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
//-------------------------------------------------------------------------

blitz::Array<double,3>
GroundCoordinateArray::ground_coor_scan_arr(int Start_line, int Number_line) const
{
  int ms = igc_->number_sample() / 2;
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc;
  tt->time(GeoCal::ImageCoordinate(Start_line, ms), t, fc);
  sl = (int) floor(fc.line + 0.5);
  if(Number_line < 0)
    el = (int) camera_slv.size();
  else
    el = std::min(sl + Number_line, (int) camera_slv.size());
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
  GeoCal::Time t;
  GeoCal::FrameCoordinate fc;
  tt->time(GeoCal::ImageCoordinate(Start_line, Sample), t, fc);
  boost::shared_ptr<GeoCal::QuaternionOrbitData> od =
    igc_->orbit_data(t, Sample);
  boost::shared_ptr<GeoCal::CartesianFixed> cf = od->position_cf();
  for(int i = sl; i < el; ++i) {
    GeoCal::CartesianFixedLookVector lv = od->cf_look_vector(camera_slv[i]);
    boost::shared_ptr<GeoCal::CartesianFixed> t;
    if(Initial_samp)
      t = igc_->dem().intersect(*cf, lv, igc_->resolution(), igc_->max_height());
    else {
      double start_dist = dist(i);
      if(i - 1 >= sl)
	start_dist = std::min(start_dist, dist(i-1));
      if(i + 1 < el)
	start_dist = std::min(start_dist, dist(i+1));
      t = igc_->dem().intersect_start_length(*cf, lv, igc_->resolution(),
					     start_dist);
    }
    t->lat_lon_height(res(i, Sample, 0), res(i, Sample, 1), res(i, Sample, 2));
    dist(i) = sqrt(sqr(t->position[0] - cf->position[0]) +
		   sqr(t->position[1] - cf->position[1]) +
		   sqr(t->position[2] - cf->position[2]));
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
  
