For V8.00/collection 3, we updated the instrument_to_sc quaternion used do describe the
orientation of the ecostress scan mirror/camera assembly.

This was done after the time correction fix in LO (error in handling the BAD time tags,
fixed in build 713).

I used "improve_fit.py" to fit 2 attitude correction (at beginning and end of data),
using the tiepoints previously found in the l1b_geo processing and stored in the 
l1b_geo_qa files. This was investigating improving geolocation in collection 3, but
one side effect was collecting the quaternions.

We run combine.py to combine the data. 
We then do a straight average of the yaw, pitch, and roll. This isn't exactly the
same as averaging the correction quaternions (see for [example](https://github.com/christophhagen/averaging-quaternions/blob/master/averageQuaternions.py)), but this
is pretty close for similiar quaternions and more direct to calculate.

We then used the original instrument_to_sc euler values (since we are correcting on
to of this).

We then calculate:

import geocal
import numpy as np
corr = np.array([ -59.83144931, -239.61809399,  189.42305812])
corr = corr * geocal.arcsecond_to_rad
sc_to_sc_corr = geocal.quat_rot("xyz", corr[1], corr[2], corr[0])
frame_to_sc = geocal.quat_rot("zyx", -5.08101e-05, 0.0082429, -0.0024712)
print(geocal.quat_to_euler((sc_to_sc_corr.conj() * frame_to_sc)))

results - [0.00024883728328547506, 0.0073246045637570655, -0.0013094213633778223]
Note the original information about the tiepoint matching and the corrections
quaterions is stored in the pickle file if we need  to go back to the original data
