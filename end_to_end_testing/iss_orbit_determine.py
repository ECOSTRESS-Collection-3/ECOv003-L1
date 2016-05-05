#! /usr/bin/env python
#
# This program is used to determine the best ISS paths to cover a set of points.

from geocal import *
import scipy

version = "1.0"
usage = '''Usage:
  iss_orbit_determine.py [options]
  iss_orbit_determine.py -h | --help
  iss_orbit_determine.py -v | --version
   
This program is used to determine the best ISS paths to cover a set 
of points.
Options:
  -h --help         
       Print this message

  -v --version      
       Print program version
'''

args = docopt_simple(usage, version=version)

orb = SpiceOrbit(SpiceOrbit.ISS_ID, "iss_spice/iss_2015.bsp")
tstart = Time.parse_time("2015-01-01T00:00:00Z")
tend = Time.parse_time("2016-01-01T00:00:00Z")

def latitude_diff(toffset, lat):
    return orb.position_cf(tstart + toffset).latitude - lat

def longitude_diff(toffset, lon):
    return orb.position_cf(tstart + toffset).longitude - lon

# Probably something more efficient, but this isn't something we will 
# run often. This takes a few minutes to run, so we save the results.

# These points are latitude, longitude of four points that cover the 
# California ASTER data we have, selected by hand.

pts = [(39.5, -122), (38, -121), (36, -118), (34, -116)]
step_size = 100.0
threshold = 1.0
allres = {}
for pt in pts:
    res = []
    for ts in np.arange(0.0, tend - tstart - 100.0, step_size):
        if(latitude_diff(ts, pt[0]) * latitude_diff(ts + step_size, pt[0]) 
           <= 0):
            t = scipy.optimize.brentq(latitude_diff, ts, ts + step_size, 
                                      args=(pt[0],))
            if(abs(longitude_diff(t, pt[1])) < threshold):
                res.append(t)
    print(pt, ":")
    print(res)
    allres[pt] = res
write_shelve("iss_time.json", allres)

