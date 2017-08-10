// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_band_to_band.h"
%}
%import "ecostress_image_ground_connection.i"
%import "geometric_model.i"
namespace Ecostress {
  GeoCal::GeometricTiePoints band_to_band_tie_points
  (const EcostressImageGroundConnection& Igc,
   int Scan_index, int Band,
   int Nline_pt=10, int Nsamp_pt=30);
}

