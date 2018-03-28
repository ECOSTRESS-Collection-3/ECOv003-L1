#ifndef ECOSTRESS_DQI_H
#define ECOSTRESS_DQI_H

namespace Ecostress {
/****************************************************************//**
  Data quality indicator values.

  DQI_GOOD   normal data, nothing wrong with it
  DQI_INTERPOLATED 
             indicates strip data that we have filled in with
             interpolated data (see ATB for details on algorithm)
  DQI_STRIPE_NOT_INTERPOLATED
             Stripe data that we could not fill in with interpolated 
             data
  DQI_BAD_OR_MISSING 
             indicates data with a bad value (e.g., negative DN)
             or missing packets. We don't bother distinguishing
             between the 2
  DQI_NOT_SEEN
             pixels where because of the difference in time that a 
	     sample is seen with each band, the ISS has moved enough
             we haven't seen the pixel. So data is missing, but by
             instrument design instead of some problem.
*******************************************************************/
  enum Dqi { DQI_GOOD = 0, DQI_INTERPOLATED = 1,
	     DQI_STRIPE_NOT_INTERPOLATED = 2,
	     DQI_BAD_OR_MISSING = 3, DQI_NOT_SEEN = 4 };

/****************************************************************//**
  Fill values used in the radiance data for various DQI values.
  Note that FILL_VALUE_STRIPED will be filled in during L1B_RAD
  processing, but we have a value to use before this stage of
  processing.
*******************************************************************/
  enum FillValue {FILL_VALUE_BAD_OR_MISSING = -9999,
		  FILL_VALUE_STRIPED = -9998,
		  FILL_VALUE_NOT_SEEN = -9997};

//-------------------------------------------------------------------------
/// Threshold that we can use to determine fill values.
/// (Note, we add a bit of pad here in case we introduce new FillValue
/// enumerations so we have a little space.
//-------------------------------------------------------------------------

  const int fill_value_threshold = -9990;
};
#endif
