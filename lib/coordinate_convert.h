#include "geocal/ogr_coordinate.h"

namespace Ecostress {
  blitz::Array<double, 2> coordinate_convert(const blitz::Array<double, 1> latitude,
					     const blitz::Array<double, 1> longitude,
					     const boost::shared_ptr<GeoCal::OgrWrapper>& ogr);
}
