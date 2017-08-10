#define ECOSTRESS_BAND_TO_BAND_H
#include "ecostress_image_ground_connection.h"
#include "geocal/geometric_model.h"

namespace Ecostress {
  GeoCal::GeometricTiePoints band_to_band_tie_points
  (const EcostressImageGroundConnection& Igc,
   int Scan_index, int Band,
   int Nline_pt=10, int Nsamp_pt=30);
}
