// -*- mode: c++; -*-
// (Not really c++, but closest emacs mode)

%include "ecostress_common.i"

%{
#include "ecostress_dqi.h"
%}
namespace Ecostress {
  enum Dqi { DQI_GOOD = 0, DQI_INTERPOLATED = 1,
	     DQI_STRIPE_NOT_INTERPOLATED = 2,
	     DQI_BAD_OR_MISSING = 3, DQI_NOT_SEEN = 4 };
  enum FillValue {FILL_VALUE_BAD_OR_MISSING = -9999,
		  FILL_VALUE_STRIPED = -9998,
		  FILL_VALUE_NOT_SEEN = -9997};
  const int fill_value_threshold = -9990;
}

// List of things "import *" will include.
%python_export("DQI_GOOD", "DQI_INTERPOLATED",
	       "DQI_STRIPE_NOT_INTERPOLATED",
	       "DQI_BAD_OR_MISSING", "DQI_NOT_SEEN",
	       "FILL_VALUE_BAD_OR_MISSING", "FILL_VALUE_STRIPED",
	       "FILL_VALUE_NOT_SEEN", "fill_value_threshold")
