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

void GroundCoordinateArray::init()
{
  b = igc_->band();
  cam = igc_->camera();
  int nl = cam->number_line(b);
  for(int i = 0; i < nl; ++i)
    camera_slv.push_back(cam->sc_look_vector(GeoCal::FrameCoordinate(i, 0), b));
}

blitz::Array<double,3>
GroundCoordinateArray::ground_coor_arr(int Start_line) const
{
        // self.res = np.empty((len(self.slv), self.igc.number_sample,3))
        // self.dist = np.empty((len(self.slv)))
        // ms = int(self.igc.number_sample / 2)
        // self.ground_coor_arr_samp(start_line, ms, 
        //                           initial_samp = True)
        // self.dist_middle = self.dist.copy()
        // for smp in range(ms + 1, self.igc.number_sample):
        //     print("Doing ", smp)
        //     self.ground_coor_arr_samp(start_line, smp)
        // self.dist[:] = self.dist_middle
        // for smp in range(ms - 1, ms - 10, -1):
        //     print("Doing ", smp)
        //     self.ground_coor_arr_samp(start_line, smp)
        // return self.res
}

void GroundCoordinateArray::ground_corr_arr_samp(int Start_line, int Sample,
						 bool initial_samp) const
{
        // t, fc = self.time_table.time(ImageCoordinate(start_line, sample))
        // od = self.igc.orbit_data(t, sample)
        // cf = od.position_cf
        // for i, sl in enumerate(self.slv):
        //     lv = od.cf_look_vector(sl)
        //     if(initial_samp):
        //         self.res[i,sample,:] = self.igc.dem.intersect(cf, lv, self.igc.resolution, 
        //                                                  self.igc.max_height).position
        //     else:
        //         start_dist = self.dist[i]
        //         if(i - 1 >= 0):
        //             start_dist = min(start_dist, self.dist[i-1])
        //         if(i + 1 < self.dist.shape[0]):
        //             start_dist = min(start_dist, self.dist[i-1])
        //         self.res[i,sample,:] = self.igc.dem.intersect_start_length(cf, lv, 
        //                                     self.igc.resolution,  start_dist).position
        //     self.dist[i] = np.linalg.norm(self.res[i,sample,:] - cf.position)
}

void GroundCoordinateArray::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "GroundCoordinateArray:\n";
  Os << "  Igc:\n";
  opad << *igc_;
  opad.strict_sync();
}
  
