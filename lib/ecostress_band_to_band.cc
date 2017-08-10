#include "ecostress_band_to_band.h"
using namespace Ecostress;


//-----------------------------------------------------------------------
/// This creates a set of GeometricTiePoints that maps between the
/// given Band and whatever Igc.band() is (e.g., the REF_BAND). We
/// attempt to form a Nline_pt x Nsamp_pt grid.
///
/// This code would be easy enough to do in python, but we do it in
/// C++ for better performance.
//-----------------------------------------------------------------------

GeoCal::GeometricTiePoints Ecostress::band_to_band_tie_points
(const EcostressImageGroundConnection& Igc,
 int Scan_index, int Band,
 int Nline_pt, int Nsamp_pt)
{
  int sline = Scan_index * Igc.number_line_scan();
  int eline = (Scan_index + 1) * Igc.number_line_scan() - 1;
  int esamp = Igc.number_sample() - 1;
  int lstep = (eline - sline) / Nline_pt;
  int sstep = esamp / Nsamp_pt;
  GeoCal::GeometricTiePoints res;
  for(int ln = sline; ln < eline + lstep; ln += lstep) {
    // Make sure we try eline, some models extrapolate badly so we
    // want to make sure to cover the full range.
    if(ln > eline)
      ln = eline;
    for(int smp = 0; smp < esamp + sstep; smp += sstep) {
      if(smp > esamp)
	smp = esamp;
      GeoCal::ImageCoordinate ric(ln, smp);
      boost::shared_ptr<GeoCal::GroundCoordinate> gp = Igc.ground_coordinate(ric);
      GeoCal::ImageCoordinate ic;
      bool success;
      Igc.image_coordinate_scan_index(*gp, Scan_index, ic, success, Band);
      if(success)
	res.add_point(ric, ic);
    }
  }
  return res;
}
