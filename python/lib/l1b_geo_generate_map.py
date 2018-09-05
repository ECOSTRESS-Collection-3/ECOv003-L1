import geocal
from ecostress_swig import *
from .misc import determine_rotated_map_igc
import os
import h5py

class L1bGeoGenerateMap(object):
    '''This generates a L1B Geo map product. Right now we leverage off of
    the L1bGeoGenerate class, since most of the work is the same. We could
    break this connection if it is ever needed, but at least currently
    we always generate the L1bGeoGenerate and optionally do the 
    L1bGeoGenerateMap.

    Like L1bGeoGenerate, to actually generate you should execute the "run"
    command. Make sure the L1bGeoGenerate run has been executed first, we rely 
    on data generated there.
    
    By default, we generate a rotated map. You can instead force a north is up
    map by setting north_up to true. Likewise, default resolution is 70 meters,
    but you can modify this.
    '''
    def __init__(self, l1b_geo_generate, l1b_rad, output_name,
                 local_granule_id = None, log_fname = None,
                 resolution = 70, north_up = False, number_subpixel = 3):
        self.l1b_geo_generate = l1b_geo_generate
        self.l1b_rad = l1b_rad
        self.output_name = output_name
        if(local_granule_id):
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(output_name)
        self.log_fname = log_fname
        self.north_up = north_up
        self.resolution = resolution
        self.number_subpixel = number_subpixel

    def run(self):
        fout = h5py.File(self.output_name, "w")
        m = self.l1b_geo_generate.m.copy_new_file(fout,
                                 self.local_granule_id, "ECO1BMAP")
        m.write()
        mi = geocal.cib01_mapinfo(self.resolution)
        lat = self.l1b_geo_generate.lat
        lon = self.l1b_geo_generate.lon
        if(not self.north_up):
            mi = determine_rotated_map_igc(self.l1b_geo_generate.igc, mi)
        res = Resampler(lat, lon, mi, self.number_subpixel, False)
        g = fout.create_group("Mapped")
        g2 = g.create_group("MapInformation")
        g2["README"] = \
'''We specify the Map Information by giving the Coordinate System
and a Affine GeoTransform. The Coordinate System is specified as 
OpeGIS Well Known Text strings(see for example
https://en.wikipedia.org/wiki/Well-known_text or 
http://www.gdal.org/gdal_datamodel.html). This is given in the
CoordinateSystem.

We also specify the Affine GeoTransform (as for example in
geotiff, see http://geotiff.maptools.org/spec/geotiff2.6.html or
GDAL, see http://www.gdal.org/gdal_datamodel.html). This is given
in the GeoTransform. We have:

longitude   = GT_0 + GT_1 * i + GT_2 * j
latitude    = GT_3 + GT_4 * i + GT_5 * j

Where (i,j) is the sample, line of the pixel (starting at 0) and longitude
and latitude are given in degrees.

Note that in addition, we have the latitude and longitude fields in
the file. This is completely redundant with the map projection information,
we supply these fields as a convenience for software that expects this
data. But you can directly calculate latitude and longitude from the map
information.
'''
        # Hardcoded for now, this is probably fine since we don't expect to
        # change the coordinate system
        g2["CoordinateSystem"] = \
'''GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
'''
        g2.create_dataset("GeoTransform", data=res.map_info.transform,
                          dtype='f8')
