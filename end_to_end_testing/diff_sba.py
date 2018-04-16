# Short script to compare "truth" to what we get out of igc_sba. Returns
# difference in pixels.

from geocal import *
from ecostress import *

igc_truth = read_shelve("igccol_truth.xml").image_ground_connection(0)
igc_sba = read_shelve("l1b_geo_run/igccol_sba.xml").image_ground_connection(0)
icin = ImageCoordinate(igc_truth.number_line / 2,
                       igc_truth.number_sample / 2)
resolution = igc_truth.resolution_meter()
print("%0.2f pixels, with pixel size %0.2f meter" %
      (distance(igc_sba.ground_coordinate(icin),
                igc_truth.ground_coordinate(icin)) / resolution,
       resolution))
