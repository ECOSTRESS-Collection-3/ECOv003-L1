#include "ecostress_band_to_band.h"
using namespace Ecostress;


//-----------------------------------------------------------------------
/// This creates a set of GeometricTiePoints that maps between the
/// given Band and whatever Igc.band() is (e.g., the REF_BAND). We
/// attempt to form a Nline_pt x Nsamp_pt grid.
///
/// This code would be easy enough to do in python, but we do it in
/// C++ for better performance.
///
/// *NOTE* The tiepoints returned are relative to the scan, not to the
/// full image (so the line number is between 0 and 255). This is what
/// we want in L1 processing because we subset the data we use in the
/// GeometricModelImage. But this might not be what you would expect
/// from the name of this function.
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
  // We aren't super sensitive to the exact height, but we do want
  // to capture gross height changes. So find height of the center
  // point, and then use for other points we calculate
  double height = Igc.ground_coordinate(GeoCal::ImageCoordinate
        (Igc.number_line() / 2.0,
	 Igc.number_sample() / 2.0))->height_reference_surface();
  for(int ln = sline; ln < eline + lstep; ln += lstep) {
    // Make sure we try eline, some models extrapolate badly so we
    // want to make sure to cover the full range.
    if(ln > eline)
      ln = eline;
    for(int smp = 0; smp < esamp + sstep; smp += sstep) {
      if(smp > esamp)
	smp = esamp;
      GeoCal::ImageCoordinate ric(ln, smp);
      boost::shared_ptr<GeoCal::GroundCoordinate> gp = Igc.ground_coordinate_approx_height(ric, height);
      GeoCal::ImageCoordinate ic;
      bool success;
      Igc.image_coordinate_scan_index(*gp, Scan_index, ic, success, Band);
      if(success) {
	// Change to being relative to scan rather than full image.
	ic.line -= sline;
	ric.line -= sline;
	res.add_point(ric, ic);
      }
    }
  }
  return res;
}
