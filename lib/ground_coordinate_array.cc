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
  tt = igc_->time_table();
  int nl = cam->number_line(b);
  for(int i = 0; i < nl; ++i)
    camera_slv.push_back(cam->sc_look_vector(GeoCal::FrameCoordinate(i, 0), b));
  dist.resize((int) camera_slv.size());
  res.resize((int) camera_slv.size(), igc_->number_sample(),3);
}

blitz::Array<double,3>
GroundCoordinateArray::ground_coor_arr(int Start_line) const
{
  int ms = igc_->number_sample() / 2;
  ground_coor_arr_samp(Start_line, ms, true);
  blitz::Array<double, 1> dist_middle(dist.copy());
  for(int smp = ms + 1; smp < igc_->number_sample(); ++smp)
    ground_coor_arr_samp(Start_line, smp);
  dist = dist_middle;
  for(int smp = ms - 1; smp >= 0; --smp)
    ground_coor_arr_samp(Start_line, smp);
  return res;
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
  for(int i = 0; i < (int) camera_slv.size(); ++i) {
    GeoCal::CartesianFixedLookVector lv = od->cf_look_vector(camera_slv[i]);
    boost::shared_ptr<GeoCal::CartesianFixed> t;
    if(Initial_samp)
      t = igc_->dem().intersect(*cf, lv, igc_->resolution(), igc_->max_height());
    else {
      double start_dist = dist(i);
      if(i - 1 >= 0)
	start_dist = std::min(start_dist, dist(i-1));
      if(i + 1 < (int) dist.size())
	start_dist = std::min(start_dist, dist(i+1));
      t = igc_->dem().intersect_start_length(*cf, lv, igc_->resolution(),
					     start_dist);
    }
    res(i, Sample, 0) = t->position[0];
    res(i, Sample, 1) = t->position[1];
    res(i, Sample, 2) = t->position[2];
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
  
