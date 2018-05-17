# Short script to compare "truth" to what we get out of igc_sba. Returns
# difference in pixels.

from geocal import *
from ecostress import *
import os, sys

curdir = os.path.abspath(os.path.dirname(sys.argv[0]))
for i in range(3):
    igc_truth = read_shelve("%s/igccol_truth.xml" % curdir).image_ground_connection(i)
    igc_initial = read_shelve("end_to_end_test_l1b_geo/igccol_initial.xml").image_ground_connection(i)
    igc_sba = read_shelve("end_to_end_test_l1b_geo/igccol_sba.xml").image_ground_connection(i)
    icin_full = ImageCoordinate(igc_truth.number_line / 2,
                                igc_truth.number_sample / 2)
    icin_avg = ImageCoordinate(icin_full.line / 2, icin_full.sample)
    resolution = igc_truth.resolution_meter()
    initial_dist = distance(igc_initial.ground_coordinate(icin_avg),
                            igc_truth.ground_coordinate(icin_full))
    sba_dist = distance(igc_sba.ground_coordinate(icin_avg),
                        igc_truth.ground_coordinate(icin_full))

    print("%d: %0.2f pixels (%0.2f meter), with pixel size %0.2f meter, initial error %0.2f pixels (%0.2f meter)" %
          (i + 1, sba_dist / resolution, sba_dist, resolution,
           initial_dist/ resolution, initial_dist))
